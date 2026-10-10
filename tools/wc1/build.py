"""Build war.exe from the generated asm plus reconstructed C.

usage: python3 -m wc1.build [--out build/war.exe] [--legacy]

1. C files are those named by `src = "src/<file>.c"` in the symbol database;
   each is compiled with wcc386 (flags from its codegen-flags header).
2. In-place placement (default): a C object whose functions appear in the
   original in the same order and at the same relative offsets as in its
   `_TEXT` is linked at the original address of its first function, between
   asm pieces that cover the rest of the program.  Its data segments become
   zero-length anchors linked at the original address its code refers to
   (derived from the relocations; the contents are compared with the original
   and the asm keeps defining them).  All its segments are set to BYTE
   alignment (the asm pieces carry the exact padding), see
   docs/subsystems/build.md.  When the C matches (wc1.match) the image stays
   IDENTICAL.
3. Any C file that cannot be placed (functions out of order, data not
   addressable) falls back to the legacy layout: its functions are omitted
   from the asm up to their limit and the object is linked after everything
   else, so the layout shifts and the result is DIFFERENT.  `--legacy` forces
   that for every file.
4. Everything is linked with wlink (system dos4g, original stub) and compared
   with the original at the loaded-image level (wc1.compare).
"""
import argparse
import os
import struct
import subprocess
import sys

from . import analysis, emit, le, match, omf, omfpatch, path, symbols

DATA_CLASSES = ("DATA", "BSS")
# The asm emits the initialised part of the data object as segment _DATA and
# the rest as _BSS (asm/wc1.inc); a C data segment placed inside one of them is
# renamed to it so that wlink keeps it in sequence.


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit(f"failed: {' '.join(cmd)}")
    return r


class Unplaceable(Exception):
    pass


def place(p, src, obj, funcs):
    """Original placement of compiled C `obj` providing `funcs` (DB entries).
    Returns (code_range, [(data_address, segment_name)]); raises Unplaceable.
    The data segments become zero-length anchors at their original address:
    the asm keeps defining those bytes (other asm code may share them, e.g.
    merged string literals), so they are compared here instead."""
    m = omf.parse_object(obj)
    if m.comdefs:
        raise Unplaceable(f"communal variables {sorted(m.comdefs)}")
    ti, text = m.seg("_TEXT")
    if text is None:
        raise Unplaceable("no _TEXT")
    base = min(e["addr"] for e in funcs)
    for e in funcs:
        pub = m.publics.get(e["link_name"])
        if pub is None or pub[0] != ti:
            raise Unplaceable(f"{e['link_name']} not public in _TEXT")
        if e["addr"] - base != pub[1]:
            raise Unplaceable(f"{e['name']} at +{pub[1]:#x} in _TEXT, +{e['addr'] - base:#x} in the original")
    end = base + text.length
    mine = {e["addr"] for e in funcs}
    for f in p.functions:
        if base <= f["start"] < end and f["start"] not in mine:
            raise Unplaceable(f"_TEXT overlaps function {f['start']:#x}")
    dobj = p.le.obj(analysis.DATA_OBJ)
    dimg = bytes(p.image[analysis.DATA_OBJ])
    anchors = []
    for si, seg in enumerate(m.segments, 1):
        if seg.cls not in DATA_CLASSES or not seg.length:
            continue
        bases = set()
        for fu in text.fixups:
            if fu.target_kind != "seg" or fu.target != si:
                continue
            if fu.loc not in (9, 13) or fu.self_rel:
                raise Unplaceable(f"unexpected fixup kind to {seg.name}")
            orig = p.fix_at.get(base + fu.offset)
            if orig is None:
                raise Unplaceable(f"no original fixup at {base + fu.offset:#x}")
            addend = struct.unpack_from("<i", text.data, fu.offset)[0] + fu.disp
            bases.add(orig[1] - addend)
        if len(bases) != 1:
            raise Unplaceable(f"{seg.name}: original address not determined ({sorted(map(hex, bases))})")
        b = bases.pop()
        if not dobj.base <= b <= b + seg.length <= dobj.end:
            raise Unplaceable(f"{seg.name} at {b:#x} is outside the data object")
        if seg.cls == "DATA":
            want = bytearray(dimg[b - dobj.base:b - dobj.base + seg.length])
            got = bytearray(seg.data)
            for fu in seg.fixups:          # pointer fields: compared by wc1.match
                for k in range(fu.size):
                    if fu.offset + k < len(got):
                        got[fu.offset + k] = want[fu.offset + k] = 0
            if got != want:
                raise Unplaceable(f"{seg.name} contents differ from the original at {b:#x}")
        anchors.append((b, seg.name))
    if len({a for a, _ in anchors}) > 1:
        raise Unplaceable(f"data segments at several addresses {[hex(a) for a, _ in anchors]}")
    return (base, end), anchors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=path("build", "war.exe"))
    ap.add_argument("--cflags", default=os.environ.get("WC1_CFLAGS"),
                    help="override every file's codegen-flags header / the default")
    ap.add_argument("--legacy", action="store_true", help="never place C objects in sequence")
    a = ap.parse_args()
    bdir = path("build")
    odir = os.path.join(bdir, "obj")
    pdir = os.path.join(bdir, "pieces")
    os.makedirs(odir, exist_ok=True)
    os.makedirs(pdir, exist_ok=True)
    for f in os.listdir(pdir):
        os.remove(os.path.join(pdir, f))

    funcs, datas, _ = symbols.load()
    names = {e["addr"]: e["link_name"] for t in (datas, funcs) for e in t.values()}
    by_src = {}
    for e in funcs.values():
        if e.get("src"):
            by_src.setdefault(e["src"], []).append(e)
    rawfile = path("analysis", "raw_insns.txt")
    force = {int(l.split()[0], 16) for l in open(rawfile) if l.strip() and not l.startswith("#")}
    p = analysis.run()
    code, data = p.le.obj(analysis.CODE_OBJ), p.le.obj(analysis.DATA_OBJ)

    # compile, then place what can be placed
    placed, legacy = [], []        # (src, obj, code_range, [(data_range, seg)]), (src, obj, funcs)
    for src in sorted(by_src):
        o = os.path.join(odir, os.path.splitext(src)[0].replace("/", "_") + ".obj")
        match.compile_c(path(src), a.cflags, o)
        if a.legacy:
            legacy.append((src, o, by_src[src]))
            continue
        try:
            cr, drs = place(p, src, o, by_src[src])
        except Unplaceable as ex:
            print(f"legacy layout for {src}: {ex}")
            legacy.append((src, o, by_src[src]))
            continue
        placed.append((src, o, cr, drs))
    placed.sort(key=lambda x: x[2][0])

    init_end = data.base + p.data_init_size
    for src, o, cr, anchors in placed:
        rename = {}
        for addr, seg in anchors:
            region = "_DATA" if addr < init_end else "_BSS"
            if seg != region:
                rename[seg] = region
        omfpatch.patch(o, o, align="byte", rename=rename, empty={seg for _, seg in anchors})

    # the data anchors of successive C objects must be in the same order as their code
    dseq = [a_ for _, _, _, anchors in placed for a_, _ in anchors]
    if dseq != sorted(dseq):
        raise SystemExit("C objects' data anchors are not in code order")

    cuts = {cr[0]: cr[1] for _, _, cr, _ in placed}
    entries = [e["addr"] for src, _, _, _ in placed for e in by_src[src]]
    replaced = [e["addr"] for _, _, fs in legacy for e in fs]
    e = emit.Emitter(p, names=names, force_raw=force, replaced=replaced, cuts=cuts, entries=entries)

    # link sequence: piece0, C1, piece1, C2, ..., pieceN; the data pieces are
    # split at the C objects' anchors
    code_pieces, data_pieces = [], []
    ca, da = code.base, data.base
    for src, o, (cs, ce), anchors in placed:
        code_pieces.append((ca, cs) if cs > ca else None)
        if anchors:
            d = anchors[0][0]
            data_pieces.append((da, d) if d > da else None)
            da = d
        else:
            data_pieces.append(None)
        ca = ce
    code_pieces.append((ca, code.end))
    data_pieces.append((da, data.end))
    pieces = e.emit_pieces(pdir, code_pieces, data_pieces)
    seq = []
    for k, asm in enumerate(pieces):
        obj = os.path.join(pdir, os.path.basename(asm)[:-4] + ".obj")
        run(["nasm", "-O0", "-f", "obj", "-I", path("asm") + "/", "-w-number-overflow",
             "-w+error=label-orphan", "-o", obj, asm])
        seq.append(obj)
        if k < len(placed):
            seq.append(placed[k][1])
    seq += [o for _, o, _ in legacy]

    stub = os.path.join(bdir, "stub.exe")
    orig = le.load()
    with open(stub, "wb") as f:
        f.write(orig.stub)
    lnk = os.path.join(bdir, "war.lnk")
    with open(lnk, "w") as f:
        f.write("system dos4g\n")
        f.write(f"name {a.out}\n")
        for o in seq:
            f.write(f"file {o}\n")
        f.write(f"option stub={stub}\noption map={os.path.join(bdir, 'war.map')}\noption quiet\n")
    run(["wlink", f"@{lnk}"])
    n = sum(len(by_src[s]) for s in by_src)
    print(f"built {a.out}: {n} functions from {len(by_src)} C files "
          f"({len(placed)} placed in sequence, {len(legacy)} legacy layout)")
    r = subprocess.run([sys.executable, "-m", "wc1.compare", path("original", "install", "war.exe"), a.out],
                       capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1])
    if r.returncode != 0 and not legacy:
        print(r.stdout)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
