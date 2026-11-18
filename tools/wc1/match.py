"""Verify reconstructed C against the original binary, function by function.

usage: python3 -m wc1.match <file.c> [--cflags "..."] [--cc ow2|10.0a|other] [--compile-only] [-v]
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
import subprocess
import sys

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


def compile_check(srcs):
    """Every file must compile under both compilers (docs/GOAL.md, the T3
    rule): its declared one proves the match, OW2 keeps the source buildable
    by anyone.  Returns the list of (file, compiler) that failed."""
    bad = []
    d = path("build", "match", "compile-check")
    os.makedirs(d, exist_ok=True)
    for src in srcs:
        for cc in COMPILERS:
            out = os.path.join(d, cc.replace(".", "") + "_" + os.path.basename(src)[:-2] + ".obj")
            try:
                compile_c(src, None, out, cc=cc)
            except SystemExit as e:
                print(f"DOES NOT COMPILE  {src} ({cc}): {e}")
                bad.append((src, cc))
    print(f"compile check: {len(srcs)} files x {len(COMPILERS)} compilers, {len(bad)} failures")
    return bad


def main():
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
