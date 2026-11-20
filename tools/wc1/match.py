"""Verify reconstructed C against the original binary, function by function.

usage: python3 -m wc1.match <file.c> [--cflags "..."] [--cc ow2|10.0a|other] [--compile-only] [--diff [--addr HEX] [--full]] [-v]
       python3 -m wc1.match --all [-j N]   (make match-all: every src/*.c and every
                                            `src =` file, in parallel; discovery once)
       python3 -m wc1.match --compile-check [file.c ...]   (default: every src/**/*.c,
                                                           under both compilers)

The file is compiled by the compiler its `codegen-compiler:` header names
(10.0a = the original Watcom 10.0a via wc1.oldcc; no header = Open Watcom 2).

For every public function in the compiled module's _TEXT:
  1. its original address comes from the symbol database (link name);
  2. code bytes must be identical except at relocation fields;
  3. every relocation must resolve to the same target the original uses:
     - external symbols -> address from the symbol database (unknown names are
       reported together with the address the original uses, so they can be
       added with evidence);
     - module-local segments (CONST, _DATA, ...) -> one consistent base per
       segment, and the segment contents must match the original bytes there.
  4. extent: the compiled bytes run to the next public of the module's own
     object.  When that is past the original function's end - the module pads
     with alignment filler while the original image places other (possibly
     unnamed) functions there - the comparison is retried with the extent
     clamped at the original's flow end (code discovery: end of the last
     reachable instruction), provided the skipped module bytes are only
     filler (is_filler).
A function that passes all three is MATCHED: its source is a verified
reconstruction (confidence "verified", verified_by = "match:<file.c>").
"""
import argparse
import os
import re
import struct
import hashlib
import itertools
import subprocess
import sys
import threading

import capstone

from . import analysis, omf, path, symbols

BASE_CFLAGS = "-q -zl -bt=dos"
# Game code ("OPT" style, docs/subsystems/codegen.md). A source file may
# override the code-generation part with a header line
#   /* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
DEFAULT_CFLAGS = BASE_CFLAGS + " -s -ot -ol -4r -zp2"
FLAGS_RE = re.compile(r"codegen-flags:\s*(.*?)\s*(?:\*/)?$", re.M)


# The compiler a file's match is proved with (docs/subsystems/compiler.md):
#   /* codegen-compiler: 10.0a */   Watcom 10.0a, the original (wc1.oldcc, Wine)
# no header: "ow2", the Open Watcom 2 wcc386 of the dev shell.
CC_RE = re.compile(r"codegen-compiler:\s*(\S+?)\s*(?:\*/)?$", re.M)
COMPILERS = ("ow2", "10.0a")


def _head(src):
    with open(src, errors="replace") as fh:
        return fh.read(2048)


def file_cflags(src):
    """Flags for one source file: its codegen-flags header, else the default."""
    m = FLAGS_RE.search(_head(src))
    return f"{BASE_CFLAGS} {m.group(1)}" if m else DEFAULT_CFLAGS


def file_cc(src):
    """The compiler declared by the file's codegen-compiler header ("ow2" without one)."""
    m = CC_RE.search(_head(src))
    cc = m.group(1) if m else "ow2"
    if cc not in COMPILERS:
        raise SystemExit(f"{src}: unknown codegen-compiler {cc!r} (one of {', '.join(COMPILERS)})")
    return cc


def other_cc(cc):
    return "ow2" if cc == "10.0a" else "10.0a"


def compile_c(src, cflags, out, cc=None, includes=()):
    """Compile src; cflags None means the file's own flags (file_cflags), cc
    None the file's own compiler (file_cc).  `includes` are searched before
    src/include.  A failed compile raises SystemExit with the diagnostics."""
    cflags = cflags or file_cflags(src)
    cc = cc or file_cc(src)
    if cc not in COMPILERS:
        raise SystemExit(f"unknown compiler {cc!r} (one of {', '.join(COMPILERS)})")
    # Compile to a private name and rename into place: parallel runs (pytest
    # -n, match-all, build) may compile the same file to the same path.
    tmp = f"{os.path.splitext(out)[0]}~{os.getpid()}-{next(_TMP_SEQ)}.obj"
    try:
        mod = _compile_to(src, cflags, tmp, cc, includes)
        if os.path.exists(tmp):
            os.replace(tmp, out)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return mod


_TMP_SEQ = itertools.count()


def _compile_to(src, cflags, out, cc, includes):
    if cc == "10.0a":
        from . import oldcc
        try:
            return oldcc.compile_c(src, cflags, out, includes=includes)
        except oldcc.OldCCError as e:
            raise SystemExit(f"error: {e}")
    env = dict(os.environ)
    env.setdefault("INCLUDE", os.path.join(env.get("WATCOM", ""), "h"))
    ab = os.path.abspath
    cmd = ["wcc386"] + cflags.split() + [f"-i={ab(d)}" for d in includes] \
        + [f"-i={ab(path('src', 'include'))}", f"-fo={ab(out)}", ab(src)]
    # cwd: wcc386 writes <name>.err into the current directory on diagnostics
    r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                       cwd=os.path.dirname(ab(out)) or None)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit(f"compile failed: {' '.join(cmd)}")
    return omf.parse_object(out)


def orig_target(p, a, f):
    """Absolute target used by the original at fixup position a."""
    if f.self_rel:
        rel = struct.unpack_from("<i", p.cbytes, a - p.code.base)[0]
        return (a + 4 + rel) & 0xFFFFFFFF
    if a in p.fix_at:
        return p.fix_at[a][1]
    return None


_MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def is_filler(b):
    """True if b consists only of no-op alignment filler (nop, mov r,r,
    lea r,[r+0], zero padding).  Shared with wc1.codegen_sweep."""
    if set(b) == {0}:
        return True
    k = 0
    while k < len(b):
        i = next(_MD.disasm(b[k:k + 8], 0, 1), None)
        if i is None:
            return False
        ops = [x.strip() for x in i.op_str.split(",")]
        if i.mnemonic == "nop":
            pass
        elif i.mnemonic == "mov" and len(ops) == 2 and ops[0] == ops[1]:
            pass
        elif i.mnemonic == "lea" and len(ops) == 2 and re.fullmatch(
                r"\[%s(\s*\+\s*0(x0)?)?\]" % re.escape(ops[0]), ops[1]):
            pass
        else:
            return False
        k += i.size
    return True


def match_module(p, mod, funcs_by_link, verbose=False):
    text_i, text = mod.seg("_TEXT")
    if text is None:
        return []
    by_link = funcs_by_link
    # function extents inside _TEXT
    starts = sorted((off, n) for n, (si, off) in list(mod.publics.items()) + list(mod.statics.items())
                    if si == text_i)
    seg_base = {}   # module segment index -> original absolute base (derived)
    results = []
    # original functions from code discovery, for the extent retry below
    orig_fn = {f["start"]: f for f in (getattr(p, "functions", None) or [])}

    def check(lo, hi):
        """Compare the compiled bytes [lo, hi) against the original at base."""
        problems = []
        fx = {fu.offset: fu for fu in text.fixups if lo <= fu.offset < hi}
        mask = set()
        for o, fu in fx.items():
            mask.update(range(o, o + fu.size))
        got = bytes(text.data[lo:hi])
        want = p.cbytes[base - p.code.base:base - p.code.base + (hi - lo)]
        if len(want) != len(got):
            problems.append("function runs past the code object")
        for j in range(min(len(got), len(want))):
            if lo + j not in mask and got[j] != want[j]:
                problems.append(f"byte +{j:#x}: got {got[j]:02x} want {want[j]:02x}")
                break
        for o, fu in sorted(fx.items()):
            a = base + (o - lo)
            if fu.loc != 9:
                problems.append(f"+{o - lo:#x}: unsupported fixup location {fu.loc}")
                continue
            # Watcom stores the addend in the field (rel32: relative to the
            # end of the field, so a plain call carries 0).
            addend = struct.unpack_from("<i", text.data, o)[0] + fu.disp
            ot = orig_target(p, a, fu)
            if ot is None:
                problems.append(f"+{o - lo:#x}: original has no fixup here")
                continue
            if fu.target_kind == "ext":
                sym = fu.target
                te = by_link.get(sym)
                if te is None:
                    problems.append(f"+{o - lo:#x}: unresolved {sym} -> original uses {ot - addend:#x}")
                elif te["addr"] + addend != ot:
                    problems.append(f"+{o - lo:#x}: {sym}={te['addr']:#x}+{addend} but original "
                                    f"targets {ot:#x}")
            elif fu.target_kind == "seg":
                sb = ot - addend
                prev = seg_base.setdefault(fu.target, sb)
                if prev != sb:
                    problems.append(f"+{o - lo:#x}: segment {mod.segments[fu.target - 1].name} "
                                    f"base inconsistent ({prev:#x} vs {sb:#x})")
            else:
                problems.append(f"+{o - lo:#x}: unsupported fixup target kind {fu.target_kind}")
        return problems

    for k, (off, name) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(text.data)
        e = by_link.get(name)
        if e is None:
            results.append((name, "UNKNOWN", [f"no symbol-database entry with link name {name}"]))
            continue
        base = e["addr"]
        problems = check(off, end)
        if problems:
            # Extent retry: the module pads the function to the next public
            # of *this* object, while the original image may place other
            # (possibly unnamed) functions there.  When the original's flow
            # end (code discovery) lies inside the compiled extent and the
            # module only adds alignment filler past it, compare the
            # function's own code.
            f = orig_fn.get(base)
            if f is not None:
                hi = off + f["end"] - base
                if off < hi < end and is_filler(bytes(text.data[hi:end])) \
                        and not check(off, hi):
                    problems = []
        results.append((name, "MATCH" if not problems else "MISMATCH", problems))
    # module-local data must match where it was placed
    for si, sb in seg_base.items():
        s = mod.segments[si - 1]
        if s.name == "_TEXT":
            continue
        o = p.le.obj_at(sb)
        if o is None:
            results.append((s.name, "MISMATCH", [f"segment base {sb:#x} outside the image"]))
            continue
        img = p.image[o.index]
        want = bytes(img[sb - o.base:sb - o.base + len(s.data)])
        mask = set()
        for fu in s.fixups:
            mask.update(range(fu.offset, fu.offset + fu.size))
        bad = [j for j in range(len(s.data)) if j not in mask and s.data[j] != want[j]]
        results.append((f"[{s.name} @ {sb:#x}, {len(s.data)} bytes]",
                        "MATCH" if not bad else "MISMATCH",
                        [f"first data difference at +{bad[0]:#x}"] if bad else []))
    return results


def _compile_one(job):
    """Worker: (src, cc) -> (src, cc, None or the failure text)."""
    import contextlib
    import io
    src, cc = job
    out = unique_obj(src, "match", "compile-check", cc.replace(".", ""))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            compile_c(src, None, out, cc=cc)
    except SystemExit as e:
        return src, cc, f"{err.getvalue()}{e}"
    return src, cc, None


def compile_check(srcs, jobs=None):
    """Every file must compile under both compilers (docs/GOAL.md, the T3
    rule): its declared one proves the match, OW2 keeps the source buildable
    by anyone.  Compiles in parallel; returns the list of (file, compiler)
    that failed."""
    bad = []
    work = [(src, cc) for src in srcs for cc in COMPILERS]
    jobs = max(1, min(jobs or os.cpu_count() or 1, len(work) or 1))
    with _pool(jobs) as pool:
        for src, cc, fail in pool.imap(_compile_one, work):
            if fail is not None:
                print(f"DOES NOT COMPILE  {src} ({cc}): {fail}")
                bad.append((src, cc))
    print(f"compile check: {len(srcs)} files x {len(COMPILERS)} compilers, {len(bad)} failures")
    return bad


def all_srcs():
    """The files make match-all checks: top-level src/*.c plus every file a
    symbol entry names with `src =`."""
    funcs, _datas, _ = symbols.load()
    top = {os.path.join("src", f) for f in os.listdir(path("src")) if f.endswith(".c")}
    return sorted(top | {e["src"] for e in funcs.values() if e.get("src")})


def unique_obj(src, *sub):
    """An object path under build/<sub...>/ that is unique per source file
    (several src files share a basename, e.g. init.c), for parallel runs."""
    a, root = os.path.abspath(src), os.path.abspath(path("src"))
    if a.startswith(root + os.sep):
        name = os.path.splitext(os.path.relpath(a, root))[0].replace(os.sep, "__")
    else:               # outside src/ (tests): short, so Watcom's path limits hold
        name = os.path.splitext(os.path.basename(a))[0] + "-" + \
            hashlib.sha1(a.encode()).hexdigest()[:8]
    return path("build", *sub, name + ".obj")


def _pool(jobs, initializer=None, initargs=()):
    """A process pool: fork when this process is single-threaded (workers
    inherit the loaded state), forkserver otherwise (e.g. inside a pytest-xdist
    worker), where the initializer's arguments are pickled to each worker."""
    import multiprocessing
    try:                # OS threads, the count Python's fork() warning uses
        single = len(os.listdir("/proc/self/task")) == 1
    except OSError:
        single = threading.active_count() == 1
    method = "fork" if single else "forkserver"
    return multiprocessing.get_context(method).Pool(jobs, initializer, initargs)


_SHARED = {}            # per worker: the program and symbol map (_init_shared)


def _init_shared(p, by_link):
    _SHARED["p"], _SHARED["by_link"] = p, by_link


def _match_one(src):
    """Worker: compile src under its declared compiler and match it.
    Returns (src, ok, report text) - the same lines single-file mode prints."""
    import contextlib
    import io
    p, by_link = _SHARED["p"], _SHARED["by_link"]
    cc = file_cc(src)
    out = unique_obj(src, "match", "all", cc)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            mod = compile_c(src, None, out, cc=cc)
    except SystemExit as e:
        return src, False, f"{err.getvalue()}{e}\n"
    lines, ok = [], True
    for name, status, problems in match_module(p, mod, by_link):
        lines.append(f"{status:9} {name}")
        lines += [f"            {pr}" for pr in problems[:6]]
        ok &= status == "MATCH"
    return src, ok, "\n".join(lines) + "\n"


def match_all(srcs, jobs=None):
    """Match every file (discovery and the symbol database loaded once, the
    files spread over `jobs` worker processes).  Prints each file's report in
    order; returns the files that failed."""
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.run()
    jobs = max(1, min(jobs or os.cpu_count() or 1, len(srcs)))
    bad = []
    with _pool(jobs, _init_shared, (p, by_link)) as pool:
        for src, ok, text in pool.imap(_match_one, srcs):
            sys.stdout.write(f"== {src}\n{text}")
            sys.stdout.flush()
            if not ok:
                bad.append(src)
    print(f"match-all: {len(srcs)} files, {len(bad)} failed" +
          "".join(f"\n  FAILED {s}" for s in bad))
    return bad


_REG_RE = re.compile(
    r"\b(e?(?:ax|bx|cx|dx|si|di|bp|sp)|[abcd][hl])\b"
)
_HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")


def _trim_filler_end(data, lo, hi):
    """Trim trailing alignment filler bytes from compiled function [lo, hi)."""
    insns = list(_MD.disasm(bytes(data[lo:hi]), 0))
    while insns:
        last = insns[-1]
        if is_filler(bytes(last.bytes)):
            hi = lo + last.address
            insns.pop()
        else:
            break
    return hi


def _disasm_insns(buf, base_addr, rel_base=None):
    """Disassemble buf at base_addr; return list of dicts with offset/text/norm."""
    out = []
    rel_base = base_addr if rel_base is None else rel_base
    for i in _MD.disasm(bytes(buf), base_addr):
        off = i.address - rel_base
        op = i.op_str
        # Normalize local intra-function branch target addresses to +off
        if (i.mnemonic == "jmp" or i.mnemonic.startswith("j")) and op.startswith("0x"):
            try:
                tgt = int(op, 16)
                if 0 <= tgt - rel_base < len(buf) + 0x100:
                    op = f"+{tgt - rel_base:#x}"
            except ValueError:
                pass
        out.append({
            "addr": i.address,
            "off": off,
            "size": i.size,
            "mnem": i.mnemonic,
            "op": op,
            "text": f"{i.mnemonic} {op}".strip(),
            "bytes": bytes(i.bytes),
        })
    return out


def _classify_pair(o, g):
    """Classify a single aligned (orig, got) instruction pair."""
    if o["text"] == g["text"]:
        return "EQUAL"
    if o["mnem"] != g["mnem"]:
        return "OP/STRUCT"
    # Same mnemonic: compare register-normalized and immediate-normalized forms
    o_noreg = _REG_RE.sub("<R>", o["op"])
    g_noreg = _REG_RE.sub("<R>", g["op"])
    if o_noreg == g_noreg:
        return "REG"
    o_noimm = _HEX_RE.sub("<I>", o["op"])
    g_noimm = _HEX_RE.sub("<I>", g["op"])
    if o_noimm == g_noimm:
        return "IMM/REL"
    o_both = _HEX_RE.sub("<I>", o_noreg)
    g_both = _HEX_RE.sub("<I>", g_noreg)
    if o_both == g_both:
        return "REG"
    return "OP/STRUCT"


def _patch_got_fixups(text, off, end, base, by_link):
    """Return a copy of compiled bytes [off, end) with external fixups patched
    to their resolved DB addresses (when known), so instruction diffing does not
    treat zeroed unlinked relocations as mismatches."""
    buf = bytearray(text.data[off:end])
    for fu in text.fixups:
        if not (off <= fu.offset < end) or fu.loc != 9:
            continue
        rel_off = fu.offset - off
        if rel_off + 4 > len(buf):
            continue
        if fu.target_kind == "ext":
            te = by_link.get(fu.target)
            if te is None:
                continue
            addend = struct.unpack_from("<i", buf, rel_off)[0] + fu.disp
            if fu.self_rel:
                val = te["addr"] + addend - (base + rel_off + 4)
            else:
                val = te["addr"] + addend
            struct.pack_into("<I", buf, rel_off, val & 0xFFFFFFFF)
    return bytes(buf)


def diff_function(p, mod, by_link, name=None, orig_addr=None, context=3):
    """Instruction-level diff between one compiled function in `mod` and the original.

    Returns a dict:
      name, orig_addr, matched, status, problems,
      score: (op_diffs, imm_diffs, reg_diffs, insn_len_diff, byte_len_diff),
      first_diff: compact string (or None if matched),
      lines: compact diff lines (context around mismatches),
      full_orig / full_got: instruction listings.
    """
    import difflib
    text_i, text = mod.seg("_TEXT")
    if text is None:
        return {"name": name or "?", "orig_addr": orig_addr, "matched": False,
                "status": "NO_TEXT", "problems": ["no _TEXT segment"],
                "score": (9999, 0, 0, 0, 0), "first_diff": "no _TEXT segment",
                "lines": [], "full_orig": [], "full_got": []}
    starts = sorted((off, n) for n, (si, off) in list(mod.publics.items()) + list(mod.statics.items())
                    if si == text_i)
    if not starts:
        return {"name": name or "?", "orig_addr": orig_addr, "matched": False,
                "status": "EMPTY", "problems": ["no functions in _TEXT"],
                "score": (9999, 0, 0, 0, 0), "first_diff": "no functions in _TEXT",
                "lines": [], "full_orig": [], "full_got": []}
    idx = 0
    if name is not None:
        for k, (_o, n) in enumerate(starts):
            if n == name or n.rstrip("_").lstrip("_") == name.rstrip("_").lstrip("_"):
                idx = k
                break
    off, fn_name = starts[idx]
    end = starts[idx + 1][0] if idx + 1 < len(starts) else len(text.data)
    end_trimmed = _trim_filler_end(text.data, off, end)

    e = by_link.get(fn_name)
    base = orig_addr if orig_addr is not None else (e["addr"] if e else None)
    if base is None:
        return {"name": fn_name, "orig_addr": None, "matched": False,
                "status": "UNKNOWN", "problems": [f"no symbol-database entry for {fn_name}"],
                "score": (9999, 0, 0, 0, 0), "first_diff": f"unknown symbol {fn_name}",
                "lines": [], "full_orig": [], "full_got": []}

    # Exact match check first (reuses match_module logic when symbol is in DB)
    matched = False
    status = "MISMATCH"
    problems = []
    if orig_addr is None or (e and e["addr"] == orig_addr):
        for n, st, probs in match_module(p, mod, by_link):
            if n == fn_name:
                status, problems = st, probs
                matched = (st == "MATCH")
                break
    orig_fn = {f["start"]: f for f in (getattr(p, "functions", None) or [])}
    f_info = orig_fn.get(base)
    orig_len = (f_info["end"] - base) if f_info else (end_trimmed - off)
    orig_buf = bytes(p.cbytes[base - p.code.base: base - p.code.base + orig_len])
    got_buf = _patch_got_fixups(text, off, end_trimmed, base, by_link)

    orig_ins = _disasm_insns(orig_buf, base, rel_base=base)
    got_ins = _disasm_insns(got_buf, base, rel_base=base)

    # Align by normalized mnemonic + register-abstracted operand shape
    o_keys = [f"{i['mnem']} {_HEX_RE.sub('<I>', _REG_RE.sub('<R>', i['op']))}" for i in orig_ins]
    g_keys = [f"{i['mnem']} {_HEX_RE.sub('<I>', _REG_RE.sub('<R>', i['op']))}" for i in got_ins]
    sm = difflib.SequenceMatcher(None, o_keys, g_keys, autojunk=False)

    op_diffs = imm_diffs = reg_diffs = 0
    first_diff = None
    rows = []  # (tag, orig_i_or_None, got_i_or_None)
    for op_tag, i1, i2, j1, j2 in sm.get_opcodes():
        if op_tag == "equal":
            for oi, gi in zip(orig_ins[i1:i2], got_ins[j1:j2]):
                cls = _classify_pair(oi, gi)
                if cls == "REG":
                    reg_diffs += 1
                elif cls == "IMM/REL":
                    imm_diffs += 1
                elif cls == "OP/STRUCT":
                    op_diffs += 1
                if cls != "EQUAL" and first_diff is None:
                    first_diff = (f"orig {oi['addr']:#x} ({oi['text']}) vs "
                                  f"got +{gi['off']:#x} ({gi['text']}) [{cls}]")
                rows.append((cls, oi, gi))
        else:
            m = min(i2 - i1, j2 - j1)
            for k in range(m):
                oi, gi = orig_ins[i1 + k], got_ins[j1 + k]
                cls = _classify_pair(oi, gi)
                if cls == "REG":
                    reg_diffs += 1
                elif cls == "IMM/REL":
                    imm_diffs += 1
                else:
                    op_diffs += 1
                if first_diff is None:
                    first_diff = (f"orig {oi['addr']:#x} ({oi['text']}) vs "
                                  f"got +{gi['off']:#x} ({gi['text']}) [{cls}]")
                rows.append((cls, oi, gi))
            for oi in orig_ins[i1 + m:i2]:
                op_diffs += 1
                if first_diff is None:
                    first_diff = f"orig {oi['addr']:#x} ({oi['text']}) missing in compiled [OP/STRUCT]"
                rows.append(("DEL", oi, None))
            for gi in got_ins[j1 + m:j2]:
                op_diffs += 1
                if first_diff is None:
                    first_diff = f"extra compiled +{gi['off']:#x} ({gi['text']}) [OP/STRUCT]"
                rows.append(("ADD", None, gi))

    if matched:
        score = (0, 0, 0, 0, 0)
        first_diff = None
    else:
        score = (op_diffs, imm_diffs, reg_diffs, abs(len(orig_ins) - len(got_ins)),
                 abs(len(orig_buf) - len(got_buf)))
        if first_diff is None and problems:
            first_diff = problems[0]

    # Build compact diff view (context lines around non-EQUAL rows)
    show = set()
    for idx_r, (tag, _o, _g) in enumerate(rows):
        if tag != "EQUAL":
            for k in range(max(0, idx_r - context), min(len(rows), idx_r + context + 1)):
                show.add(k)
    diff_lines = []
    prev = -1
    for idx_r in sorted(show):
        if prev >= 0 and idx_r > prev + 1:
            diff_lines.append("  ...")
        tag, oi, gi = rows[idx_r]
        if tag == "EQUAL":
            diff_lines.append(f"  {oi['addr']:05x}  {oi['text']}")
        elif tag == "DEL":
            diff_lines.append(f"- {oi['addr']:05x}  {oi['text']}   [ORIG ONLY]")
        elif tag == "ADD":
            diff_lines.append(f"+ +{gi['off']:04x}  {gi['text']}   [GOT ONLY]")
        else:
            diff_lines.append(f"! {oi['addr']:05x}  {oi['text']:36s} | +{gi['off']:04x}  {gi['text']}  [{tag}]")
        prev = idx_r

    return {
        "name": fn_name,
        "orig_addr": base,
        "matched": matched,
        "status": status,
        "problems": problems,
        "score": score,
        "counts": {"op": op_diffs, "imm": imm_diffs, "reg": reg_diffs,
                   "orig_insns": len(orig_ins), "got_insns": len(got_ins)},
        "first_diff": first_diff,
        "lines": diff_lines,
        "full_orig": [f"{i['addr']:05x}  {i['text']}" for i in orig_ins],
        "full_got": [f"+{i['off']:04x}  {i['text']}" for i in got_ins],
    }


def main():
    if sys.argv[1:2] == ["--all"]:
        ap = argparse.ArgumentParser(prog="wc1.match --all")
        ap.add_argument("-j", "--jobs", type=int, default=None)
        a = ap.parse_args(sys.argv[2:])
        return 1 if match_all(all_srcs(), a.jobs) else 0
    if sys.argv[1:2] == ["--compile-check"]:
        srcs = sys.argv[2:] or sorted(
            os.path.join(dp, f) for dp, _d, fs in os.walk(path("src")) for f in fs if f.endswith(".c"))
        return 1 if compile_check(srcs) else 0
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--cflags", default=os.environ.get("WC1_CFLAGS"),
                    help="override the file's codegen-flags header / the default")
    ap.add_argument("--cc", choices=COMPILERS + ("other",),
                    help="override the file's codegen-compiler header; 'other' = the "
                         "compiler it does not declare")
    ap.add_argument("--compile-only", action="store_true",
                    help="only check that the file compiles (with --cc other: under both)")
    ap.add_argument("--diff", action="store_true",
                    help="print side-by-side instruction diff and first-divergence summary")
    ap.add_argument("--addr", default=None,
                    help="override original function address (hex) for --diff")
    ap.add_argument("--full", action="store_true",
                    help="with --diff, also print full original and compiled instruction listings")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    cc = other_cc(file_cc(a.src)) if a.cc == "other" else (a.cc or file_cc(a.src))
    os.makedirs(path("build", "match", cc), exist_ok=True)
    out = path("build", "match", cc, os.path.splitext(os.path.basename(a.src))[0] + ".obj")
    mod = compile_c(a.src, a.cflags, out, cc=cc)
    if a.compile_only:
        print(f"COMPILES  {a.src} ({cc})")
        return 0
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.run()          # discovery + partition: p.functions has flow ends
    if a.diff:
        orig_addr = int(a.addr, 16) if a.addr else None
        text_i, _text = mod.seg("_TEXT")
        fn_names = [n for _, n in sorted(
            (off, n) for n, (si, off) in mod.publics.items() if si == text_i)]
        ok = True
        for fn_name in fn_names:
            d = diff_function(p, mod, by_link, name=fn_name,
                              orig_addr=orig_addr if len(fn_names) == 1 else None)
            c = d["counts"]
            print(f"{d['status']:9} {d['name']} (orig={c['orig_insns']} got={c['got_insns']} insns, "
                  f"op={c['op']} imm={c['imm']} reg={c['reg']})")
            if d["first_diff"]:
                print(f"  first_diff: {d['first_diff']}")
            for pr in d["problems"][: (None if a.v else 4)]:
                print(f"  problem:    {pr}")
            if d["lines"]:
                print("\n".join(d["lines"][: (None if a.v else 60)]))
            if a.full:
                print("-- ORIG --\n" + "\n".join(d["full_orig"]))
                print("-- GOT  --\n" + "\n".join(d["full_got"]))
            ok &= d["matched"]
        return 0 if ok else 1
    res = match_module(p, mod, by_link, a.v)
    ok = True
    for name, status, problems in res:
        print(f"{status:9} {name}")
        for pr in problems[: (None if a.v else 6)]:
            print(f"            {pr}")
        ok &= status == "MATCH"
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
