"""Lightweight local Watcom 10.0a permuter / flag-and-idiom searcher.

Tries compiler flag presets and targeted Watcom 10.0a C source mutations
(local declaration order, int/short/unsigned widths, ++i/i++, volatile casts)
in parallel (worker threads, each compile its own wcc386 process), scored by
wc1.match.diff_function().  Zero LLM tokens.  Deterministic: the earliest
matching candidate wins.  Bounded: each compile gets --timeout s (default 60,
stricter on purpose than oldcc's own 180 s, since a candidate is cheap to
drop) and the whole search --wall-budget s (default 900; result
stopped="deadline").  The first compile timeout (stuck Wine/wcc386) stops the
search (stopped="timeout", env_error set, CLI exit 2) instead of trying more:
every later candidate would hang the same way.

usage: python3 -m wc1.permuter <file.c> [--apply] [--max-trials 80]
                               [--jobs N] [--addr HEX] [--rounds 2]
                               [--timeout S] [--wall-budget S]
"""
import argparse
import concurrent.futures
import hashlib
import itertools
import os
import re
import sys
import threading
import time

from . import analysis, match, path, symbols

FLAG_PRESETS = [
    ("10.0a", "-s -ot -ol -4r -zp2"),       # default OPT (c01)
    ("10.0a", "-s -ot -ol -5r -zp2"),       # E7 c06: Pentium OPT (minimal -4r->-5r diff; 11 buildable)
    ("10.0a", "-s -ot -oa -ol -5r -zp2"),   # E7 c07: Pentium OPT + -oa (Tier 1 #1 marginal)
    ("10.0a", "-s -ot -ol -5r -d1+ -zp2"),  # E7 c19: Pentium DBG (Tier 1 #2 marginal; 2 buildable)
    ("10.0a", "-s -ot -oa -ol -4r -zp2"),   # existing (c02)
    ("10.0a", "-s -ot -ol -4r -d1+ -zp2"),  # existing (c18)
    ("10.0a", "-s -od -4r -zp2"),           # existing (c20)
    ("10.0a", "-s -od -4r -d1+ -zp2"),      # existing (c21)
    ("10.0a", "-s -os -ol -4r -zp2"),       # existing (c05)
    ("10.0a", "-s -os -4r -zp2"),           # E7 c22: completes Tier 1 (+21 marginal improved)
    ("10.0a", "-s -ot -4r -zp2"),           # existing (c03)
    ("10.0a", "-s -ot -oa -4r -zp2"),       # existing (c04)
    ("10.0a", "-s -ot -ol -3r -zp2"),       # E7 c10: Tier 2 (+7 marginal, 46 improved)
    ("10.0a", "-s -ot -ol -4r -of+ -zp2"),  # E7 c26: Tier 2 (+4 marginal, 30 improved)
    ("ow2",   "-s -ot -ol -4r -zp2"),       # native Open Watcom 2 fallback
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


CANDIDATE_TIMEOUT = 60      # s per candidate compile (well above a healthy one)
WALL_BUDGET = 900           # s per permute_file call; checked before each submission
_FAIL_SCORE = (99999, 0, 0, 0, 0)


class _Res(tuple):
    """(matched, score, label, cc, cflags, text, first_diff) + .status
    ("ok", "fail" or "timeout")."""
    def __new__(cls, fields, status="ok"):
        self = super().__new__(cls, fields)
        self.status = status
        return self


def _eval_candidate(ctx, job):
    """Compile one (label, cc, cflags_short, text) candidate and return a _Res.

    Never raises: a failed compile or any other error scores as a failed
    candidate; a compile timeout comes back with status "timeout".  Runs in a
    worker thread (each compile is its own wcc386 process), so the temp names
    carry the thread id and the compile is quiet (no stderr redirection,
    which is process-wide)."""
    label, cc, cflags_short, text = job
    h = hashlib.sha1(f"{cc}|{cflags_short}|{text}".encode()).hexdigest()[:12]
    work = path("build", "permuter")
    tag = f"cand_{os.getpid()}_{threading.get_ident()}_{h}"
    c_path = os.path.join(work, tag + ".c")
    o_path = os.path.join(work, tag + ".obj")
    full_flags = f"{match.BASE_CFLAGS} {cflags_short}"

    def fail(why, status="fail"):
        return _Res((False, _FAIL_SCORE, label, cc, cflags_short, text, why), status)

    try:
        os.makedirs(work, exist_ok=True)
        with open(c_path, "w") as fh:
            fh.write(text)
        mod = match.compile_c(c_path, full_flags, o_path, cc=cc, includes=(ctx["src_dir"],),
                              timeout=ctx["timeout"], quiet=True)
        with ctx["lock"]:   # capstone/diff state is shared; compiles are the slow part
            d = match.diff_function(ctx["p"], mod, ctx["by_link"], orig_addr=ctx["orig_addr"])
        return _Res((d["matched"], d["score"], label, cc, cflags_short, text, d["first_diff"]))
    except match.CompileTimeout as e:
        return fail(f"compile timed out: {e}", "timeout")
    except SystemExit:
        return fail("compile failed")
    except Exception as e:  # noqa: BLE001 - one bad candidate must not end the search
        return fail(f"candidate error: {type(e).__name__}: {e}")
    finally:
        for fp in (c_path, o_path, os.path.splitext(c_path)[0] + ".err", o_path + ".log"):
            try:
                os.unlink(fp)
            except OSError:
                pass


def _better(res, best):
    """True if res beats best: a match beats a miss, else a strictly lower
    score (ties keep the earlier candidate)."""
    if best is None:
        return True
    if best[0]:
        return False
    return bool(res[0]) or res[1] < best[1]


def _run_batch(ctx, ex, jobs, batch, deadline, tick):
    """Evaluate `batch` in list order with at most `jobs` in flight.

    Stops submitting on the first match, compile timeout or past `deadline`,
    then waits for the compiles already running (each bounded by its own
    timeout).  Because candidates are submitted in order, every candidate
    before a match has been evaluated, so the earliest match in list order is
    the winner whatever order the compiles finish in.  Returns (best, stop):
    stop is None, "match", "timeout" or "deadline"."""
    results = {}
    inflight = {}
    todo = iter(enumerate(batch))
    stop = None
    while True:
        while stop is None and len(inflight) < jobs:
            if time.monotonic() > deadline:
                stop = "deadline"
                break
            nxt = next(todo, None)
            if nxt is None:
                break
            i, job = nxt
            inflight[ex.submit(_eval_candidate, ctx, job)] = i
        if not inflight:
            break
        done, _ = concurrent.futures.wait(inflight, return_when=concurrent.futures.FIRST_COMPLETED)
        for fut in done:
            i = inflight.pop(fut)
            res = fut.result()
            results[i] = res
            tick(res)
            if res.status == "timeout":
                stop = "timeout"
            elif res[0] and stop is None:
                stop = "match"
    best = None
    for i in sorted(results):
        if _better(results[i], best):
            best = results[i]
    return best, stop


def permute_file(src, max_trials=80, jobs=None, orig_addr=None, rounds=2, apply=False,
                 timeout=CANDIDATE_TIMEOUT, wall_budget=WALL_BUDGET, on_progress=None):
    """Run flag sweep + mutation hill-climbing on `src`. Returns result dict.

    The baseline (the file as it is) is compiled first, on its own: a file
    that already matches wins without trying anything else.  The first compile that runs
    past `timeout` seconds stops the whole search (a stuck Wine makes every
    later compile stall too) and the result carries `env_error`; no new
    candidate starts after `wall_budget` seconds (`stopped` == "deadline").  `on_progress(trials,
    label)` is called after each evaluated candidate (a heartbeat)."""
    t0 = time.monotonic()
    deadline = t0 + wall_budget
    src_abs = os.path.abspath(src)
    src_dir = os.path.dirname(src_abs)
    with open(src_abs, errors="replace") as fh:
        base_text = fh.read()

    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    ctx = {"p": analysis.run(), "by_link": by_link, "src_dir": src_dir,
           "orig_addr": orig_addr, "timeout": timeout, "lock": threading.Lock()}

    cur_cc = match.file_cc(src_abs)
    cur_flags = match.file_cflags(src_abs).replace(match.BASE_CFLAGS, "").strip()

    jobs = max(1, min(jobs or os.cpu_count() or 1, 8))
    trials = 0

    def tick(res):
        nonlocal trials
        trials += 1
        if on_progress is not None:
            try:
                on_progress(trials, res[2])
            except Exception:  # noqa: BLE001 - a heartbeat must not end the search
                pass

    # Stage 0: the baseline, synchronously
    best = _eval_candidate(ctx, ("baseline", cur_cc, cur_flags, base_text))
    tick(best)
    stop = "timeout" if best.status == "timeout" else ("match" if best[0] else None)

    # Stage 1: flag presets
    stage1 = []
    seen_preset = {(cur_cc, cur_flags)}
    for cc, fl in FLAG_PRESETS:
        if (cc, fl) not in seen_preset:
            seen_preset.add((cc, fl))
            stage1.append((f"flags({cc}:{fl})", cc, fl, set_headers(base_text, cc, fl)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs,
                                               thread_name_prefix="wc1-permuter") as ex:
        if stop is None and stage1:
            res, stop = _run_batch(ctx, ex, jobs, stage1, deadline, tick)
            if res is not None and _better(res, best):
                best = res

        # Stage 2: mutation hill-climbing rounds on best (cc, flags)
        for _ in range(rounds):
            if stop is not None or best[0]:
                break
            muts = generate_mutations(best[5], max_count=max_trials)
            if not muts:
                break
            batch = [(lbl, best[3], best[4], txt) for lbl, txt in muts]
            res, stop = _run_batch(ctx, ex, jobs, batch, deadline, tick)
            if res is None or not _better(res, best):
                break
            best = res

    env_error = None
    if stop == "timeout":
        env_error = f"compile timed out (>{timeout}s); permuter stopped after {trials} trials"

    matched, score, label, win_cc, win_flags, win_text, first_diff = best
    # a search cut short by a compile timeout writes nothing: the toolchain is
    # suspect and the caller stops the run anyway
    applied = bool(matched and apply and not env_error)
    if applied:
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
        "applied": applied,
        "text": set_headers(win_text, win_cc, win_flags),
        "env_error": env_error,
        "stopped": stop,
        "elapsed": round(time.monotonic() - t0, 2),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wc1.permuter", description=__doc__.split("\n\n")[0])
    ap.add_argument("src")
    ap.add_argument("--apply", action="store_true", help="overwrite src with winning C on exact MATCH")
    ap.add_argument("--max-trials", type=int, default=80)
    ap.add_argument("--jobs", type=int, default=None)
    ap.add_argument("--addr", default=None, help="override original address (hex)")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=CANDIDATE_TIMEOUT,
                    help="per-candidate compile timeout in s; the first timeout stops the search")
    ap.add_argument("--wall-budget", type=int, default=WALL_BUDGET,
                    help="stop submitting candidates after this many s")
    a = ap.parse_args(argv)
    orig_addr = int(a.addr, 16) if a.addr else None
    r = permute_file(a.src, max_trials=a.max_trials, jobs=a.jobs,
                     orig_addr=orig_addr, rounds=a.rounds, apply=a.apply,
                     timeout=a.timeout, wall_budget=a.wall_budget)
    if r["matched"]:
        act = " (applied)" if r["applied"] else ""
        print(f"MATCH     {r['src']} via {r['label']} [{r['cc']} {r['cflags']}] ({r['trials']} trials){act}")
        return 0
    print(f"MISMATCH  {r['src']} best={r['score']} via {r['label']} [{r['cc']} {r['cflags']}] ({r['trials']} trials)")
    if r["first_diff"]:
        print(f"  first_diff: {r['first_diff']}")
    if r["env_error"]:
        print(f"  error: {r['env_error']}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
