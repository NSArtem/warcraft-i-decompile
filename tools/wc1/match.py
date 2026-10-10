"""Verify reconstructed C against the original binary, function by function.

usage: python3 -m wc1.match <file.c> [--cflags "..."] [-v]

For every public function in the compiled module's _TEXT:
  1. its original address comes from the symbol database (link name);
  2. code bytes must be identical except at relocation fields;
  3. every relocation must resolve to the same target the original uses:
     - external symbols -> address from the symbol database (unknown names are
       reported together with the address the original uses, so they can be
       added with evidence);
     - module-local segments (CONST, _DATA, ...) -> one consistent base per
       segment, and the segment contents must match the original bytes there.
A function that passes all three is MATCHED: its source is a verified
reconstruction (confidence "verified", verified_by = "match:<file.c>").
"""
import argparse
import os
import re
import struct
import subprocess
import sys

from . import analysis, omf, path, symbols

BASE_CFLAGS = "-q -zl -bt=dos"
# Game code ("OPT" style, docs/subsystems/codegen.md). A source file may
# override the code-generation part with a header line
#   /* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
DEFAULT_CFLAGS = BASE_CFLAGS + " -s -ot -ol -4r -zp2"
FLAGS_RE = re.compile(r"codegen-flags:\s*(.*?)\s*(?:\*/)?$", re.M)


def file_cflags(src):
    """Flags for one source file: its codegen-flags header, else the default."""
    with open(src, errors="replace") as fh:
        m = FLAGS_RE.search(fh.read(2048))
    return f"{BASE_CFLAGS} {m.group(1)}" if m else DEFAULT_CFLAGS


def compile_c(src, cflags, out):
    """Compile src; cflags None means the file's own flags (file_cflags)."""
    cflags = cflags or file_cflags(src)
    env = dict(os.environ)
    env.setdefault("INCLUDE", os.path.join(env.get("WATCOM", ""), "h"))
    cmd = ["wcc386"] + cflags.split() + [f"-i={path('src', 'include')}", f"-fo={out}", src]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
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
    for k, (off, name) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(text.data)
        e = by_link.get(name)
        if e is None:
            results.append((name, "UNKNOWN", [f"no symbol-database entry with link name {name}"]))
            continue
        base = e["addr"]
        problems = []
        fx = {fu.offset: fu for fu in text.fixups if off <= fu.offset < end}
        mask = set()
        for o, fu in fx.items():
            mask.update(range(o, o + fu.size))
        got = bytes(text.data[off:end])
        want = p.cbytes[base - p.code.base:base - p.code.base + (end - off)]
        if len(want) != len(got):
            problems.append("function runs past the code object")
        for j in range(min(len(got), len(want))):
            if off + j not in mask and got[j] != want[j]:
                problems.append(f"byte +{j:#x}: got {got[j]:02x} want {want[j]:02x}")
                break
        for o, fu in sorted(fx.items()):
            a = base + (o - off)
            if fu.loc != 9:
                problems.append(f"+{o - off:#x}: unsupported fixup location {fu.loc}")
                continue
            # Watcom stores the addend in the field (rel32: relative to the
            # end of the field, so a plain call carries 0).
            addend = struct.unpack_from("<i", text.data, o)[0] + fu.disp
            ot = orig_target(p, a, fu)
            if ot is None:
                problems.append(f"+{o - off:#x}: original has no fixup here")
                continue
            if fu.target_kind == "ext":
                sym = fu.target
                te = by_link.get(sym)
                if te is None:
                    problems.append(f"+{o - off:#x}: unresolved {sym} -> original uses {ot - addend:#x}")
                elif te["addr"] + addend != ot:
                    problems.append(f"+{o - off:#x}: {sym}={te['addr']:#x}+{addend} but original "
                                    f"targets {ot:#x}")
            elif fu.target_kind == "seg":
                sb = ot - addend
                prev = seg_base.setdefault(fu.target, sb)
                if prev != sb:
                    problems.append(f"+{o - off:#x}: segment {mod.segments[fu.target - 1].name} "
                                    f"base inconsistent ({prev:#x} vs {sb:#x})")
            else:
                problems.append(f"+{o - off:#x}: unsupported fixup target kind {fu.target_kind}")
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--cflags", default=os.environ.get("WC1_CFLAGS"),
                    help="override the file's codegen-flags header / the default")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    os.makedirs(path("build", "match"), exist_ok=True)
    out = path("build", "match", os.path.splitext(os.path.basename(a.src))[0] + ".obj")
    mod = compile_c(a.src, a.cflags, out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.Program().discover()
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
