"""Lightweight local Watcom 10.0a permuter / flag-and-idiom searcher.

Tries compiler flag presets and targeted Watcom 10.0a C source mutations
(local declaration order, int/short/unsigned widths, ++i/i++, volatile casts)
in parallel across CPU cores, scored by wc1.match.diff_function().
Zero LLM tokens; ~0.13s per Watcom 10.0a compile.

usage: python3 -m wc1.permuter <file.c> [--apply] [--max-trials 80]
                               [--jobs N] [--addr HEX] [--rounds 2]
"""
import argparse
import hashlib
import itertools
import multiprocessing
import os
import re
import sys

from . import analysis, match, path, symbols

FLAG_PRESETS = [
    ("10.0a", "-s -ot -ol -4r -zp2"),
    ("10.0a", "-s -ot -oa -ol -4r -zp2"),
    ("10.0a", "-s -ot -ol -4r -d1+ -zp2"),
    ("10.0a", "-s -od -4r -zp2"),
    ("10.0a", "-s -od -4r -d1+ -zp2"),
    ("10.0a", "-s -os -ol -4r -zp2"),
    ("10.0a", "-s -ot -4r -zp2"),
    ("10.0a", "-s -ot -oa -4r -zp2"),
    ("ow2",   "-s -ot -ol -4r -zp2"),
]

_DECL_MULTI_RE = re.compile(
    r"^(?P<indent>[ \t]+)(?P<ty>(?:unsigned\s+|signed\s+)?(?:int|short|long|char)(?:\s*\*)?)"
    r"\s+(?P<vars>[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)+);\s*$",
    re.M,
)

_DECL_SINGLE_RE = re.compile(
    r"^(?P<indent>[ \t]+)(?P<ty>(?:unsigned\s+|signed\s+)?(?:int|short|long|char))"
    r"\s+(?P<var>[A-Za-z_]\w*(?:\s*=\s*[^;]+)?);\s*$"
)


def set_headers(src_text, cc, cflags_short):
    """Return src_text with codegen-compiler / codegen-flags headers set."""
    lines = src_text.splitlines(True)
    # Remove existing codegen-compiler / codegen-flags lines in top 5 lines
    head, rest = lines[:5], lines[5:]
    head = [ln for ln in head if "codegen-compiler:" not in ln and "codegen-flags:" not in ln]
    hdr = []
    if cflags_short and cflags_short != "-s -ot -ol -4r -zp2":
        hdr.append(f"/* codegen-flags: {cflags_short} */\n")
    if cc == "10.0a":
        hdr.append("/* codegen-compiler: 10.0a */\n")
    return "".join(hdr + head + rest)


def generate_mutations(src_text, max_count=80):
    """Generate deterministic Watcom 10.0a C source mutations (list of (label, text))."""
    seen = {src_text}
    out = []

    def add(label, txt):
        if txt not in seen and len(out) < max_count:
            seen.add(txt)
            out.append((label, txt))

    # 1. Permute multi-variable declaration lists: `int x, y, w, h;`
    for m in _DECL_MULTI_RE.finditer(src_text):
        vlist = [v.strip() for v in m.group("vars").split(",")]
        if len(vlist) < 2:
            continue
        # Cap permutations for >4 vars (full perms up to 4! = 24, else pairwise swaps + reverses)
        if len(vlist) <= 4:
            perms = list(itertools.permutations(vlist))
        else:
            perms = [tuple(reversed(vlist))]
            for i in range(len(vlist)):
                for j in range(i + 1, len(vlist)):
                    p = list(vlist)
                    p[i], p[j] = p[j], p[i]
                    perms.append(tuple(p))
        for perm in perms[:24]:
            if list(perm) == vlist:
                continue
            repl = f"{m.group('indent')}{m.group('ty')} {', '.join(perm)};"
            add(f"perm({','.join(perm)})", src_text[:m.start()] + repl + src_text[m.end():])

    # 2. Swap adjacent simple local declaration lines inside function bodies
    lines = src_text.splitlines(True)
    decl_idxs = [i for i, ln in enumerate(lines) if _DECL_SINGLE_RE.match(ln)]
    for a, b in zip(decl_idxs, decl_idxs[1:]):
        if b == a + 1:
            swapped = list(lines)
            swapped[a], swapped[b] = swapped[b], swapped[a]
            add(f"swap_decl(L{a+1},L{b+1})", "".join(swapped))

    # 3. Toggle local integer widths (int <-> short, signed <-> unsigned)
    for i in decl_idxs:
        m = _DECL_SINGLE_RE.match(lines[i])
        if not m:
            continue
        ty = " ".join(m.group("ty").split())
        alts = {
            "int": ("short", "unsigned int", "unsigned short"),
            "unsigned int": ("int", "unsigned short", "short"),
            "short": ("int", "unsigned short", "unsigned int"),
            "unsigned short": ("short", "unsigned int", "int"),
            "char": ("unsigned char", "int"),
            "unsigned char": ("char", "int"),
        }.get(ty, ())
        for alt in alts:
            nl = list(lines)
            nl[i] = f"{m.group('indent')}{alt} {m.group('var')};\n"
            add(f"type(L{i+1}:{ty}->{alt})", "".join(nl))

    # 4. Pre/post increment swaps (`i++` <-> `++i`)
    for m in re.finditer(r"\b([A-Za-z_]\w*)\+\+", src_text):
        add(f"preinc({m.group(1)})", src_text[:m.start()] + f"++{m.group(1)}" + src_text[m.end():])
    for m in re.finditer(r"\+\+([A-Za-z_]\w*)\b", src_text):
        add(f"postinc({m.group(1)})", src_text[:m.start()] + f"{m.group(1)}++" + src_text[m.end():])

    # 5. Reverse short-lived `!= 0` / `== 0` idioms
    for m in re.finditer(r"(\b[A-Za-z_]\w*)\s*!=\s*0\b", src_text):
        add(f"truthy({m.group(1)})", src_text[:m.start()] + m.group(1) + src_text[m.end():])

    return out


_W = {}


def _worker_init(p, by_link, src_dir, orig_addr):
    _W["p"] = p
    _W["by_link"] = by_link
    _W["src_dir"] = src_dir
    _W["orig_addr"] = orig_addr


def _eval_candidate(job):
    """Compile one (label, cc, cflags_short, text) candidate and return score + diff."""
    label, cc, cflags_short, text = job
    p = _W["p"]
    by_link = _W["by_link"]
    src_dir = _W["src_dir"]
    orig_addr = _W["orig_addr"]
    h = hashlib.sha1(f"{cc}|{cflags_short}|{text}".encode()).hexdigest()[:12]
    work = path("build", "permuter")
    os.makedirs(work, exist_ok=True)
    c_path = os.path.join(work, f"cand_{os.getpid()}_{h}.c")
    o_path = os.path.join(work, f"cand_{os.getpid()}_{h}.obj")
    full_flags = f"{match.BASE_CFLAGS} {cflags_short}"
    try:
        with open(c_path, "w") as fh:
            fh.write(text)
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
            mod = match.compile_c(c_path, full_flags, o_path, cc=cc, includes=(src_dir,))
        d = match.diff_function(p, mod, by_link, orig_addr=orig_addr)
        return (d["matched"], d["score"], label, cc, cflags_short, text, d["first_diff"])
    except SystemExit:
        return (False, (99999, 0, 0, 0, 0), label, cc, cflags_short, text, "compile failed")
    finally:
        for fp in (c_path, o_path, os.path.splitext(c_path)[0] + ".err"):
            if os.path.exists(fp):
                try:
                    os.unlink(fp)
                except OSError:
                    pass


def permute_file(src, max_trials=80, jobs=None, orig_addr=None, rounds=2, apply=False):
    """Run flag sweep + mutation hill-climbing on `src`. Returns result dict."""
    src_abs = os.path.abspath(src)
    src_dir = os.path.dirname(src_abs)
    with open(src_abs, errors="replace") as fh:
        base_text = fh.read()

    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.run()

    cur_cc = match.file_cc(src_abs)
    cur_flags = match.file_cflags(src_abs).replace(match.BASE_CFLAGS, "").strip()

    jobs = max(1, min(jobs or os.cpu_count() or 1, 8))

    # Stage 0 + 1: baseline + flag presets
    stage1 = [("baseline", cur_cc, cur_flags, base_text)]
    seen_preset = {(cur_cc, cur_flags)}
    for cc, fl in FLAG_PRESETS:
        if (cc, fl) not in seen_preset:
            seen_preset.add((cc, fl))
            stage1.append((f"flags({cc}:{fl})", cc, fl, set_headers(base_text, cc, fl)))

    trials = 0
    best = None
    with match._pool(min(jobs, len(stage1)), _worker_init, (p, by_link, src_dir, orig_addr)) as pool:
        for res in pool.imap_unordered(_eval_candidate, stage1):
            trials += 1
            if best is None or (not best[0] and (res[0] or res[1] < best[1])):
                best = res
            if res[0]:
                break

    # Stage 2: mutation hill-climbing rounds on best (cc, flags)
    if not best[0]:
        for r_idx in range(rounds):
            muts = generate_mutations(best[5], max_count=max_trials)
            if not muts:
                break
            batch = [(lbl, best[3], best[4], txt) for lbl, txt in muts]
            improved = False
            with match._pool(min(jobs, len(batch)), _worker_init, (p, by_link, src_dir, orig_addr)) as pool:
                for res in pool.imap_unordered(_eval_candidate, batch):
                    trials += 1
                    if res[0] or (not best[0] and res[1] < best[1]):
                        best = res
                        improved = True
                    if res[0]:
                        pool.terminate()
                        break
            if best[0] or not improved:
                break

    matched, score, label, win_cc, win_flags, win_text, first_diff = best
    if matched and apply:
        final_text = set_headers(win_text, win_cc, win_flags)
        with open(src_abs, "w") as fh:
            fh.write(final_text)

    return {
        "src": src,
        "matched": matched,
        "score": score,
        "label": label,
        "cc": win_cc,
        "cflags": win_flags,
        "trials": trials,
        "first_diff": first_diff,
        "applied": bool(matched and apply),
        "text": set_headers(win_text, win_cc, win_flags),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wc1.permuter", description=__doc__.split("\n\n")[0])
    ap.add_argument("src")
    ap.add_argument("--apply", action="store_true", help="overwrite src with winning C on exact MATCH")
    ap.add_argument("--max-trials", type=int, default=80)
    ap.add_argument("--jobs", type=int, default=None)
    ap.add_argument("--addr", default=None, help="override original address (hex)")
    ap.add_argument("--rounds", type=int, default=2)
    a = ap.parse_args(argv)
    orig_addr = int(a.addr, 16) if a.addr else None
    r = permute_file(a.src, max_trials=a.max_trials, jobs=a.jobs,
                     orig_addr=orig_addr, rounds=a.rounds, apply=a.apply)
    if r["matched"]:
        act = " (applied)" if r["applied"] else ""
        print(f"MATCH     {r['src']} via {r['label']} [{r['cc']} {r['cflags']}] ({r['trials']} trials){act}")
        return 0
    print(f"MISMATCH  {r['src']} best={r['score']} via {r['label']} [{r['cc']} {r['cflags']}] ({r['trials']} trials)")
    if r["first_diff"]:
        print(f"  first_diff: {r['first_diff']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
