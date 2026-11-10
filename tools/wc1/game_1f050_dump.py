"""Dump every function of range 0x1f050..0x23ec0 as symbolic asm in one run
(wc1.func loads the analysis per call; this does it once). Output:
build/game_1f050/all.txt with xref summary (callers) per function."""
import sys

from . import analysis, emit, symbols

LO, HI = 0x1f050, 0x23ec0


def main():
    p = analysis.run()
    funcs, datas, _ = symbols.load(strict=False)
    names = {e["addr"]: e["link_name"] for t in (datas, funcs) for e in t.values()}
    e = emit.Emitter(p, names=names)
    out = open(sys.argv[1] if len(sys.argv) > 1 else "build/game_1f050/all.txt", "w")
    fl = sorted(p.functions, key=lambda f: f["start"])
    # callers
    callers = {}
    for f in fl:
        x = f["start"]
        while x < f["limit"]:
            i = p.insns.get(x)
            if i is None:
                x += 1
                continue
            if i.mnemonic == "call":
                try:
                    t = int(i.op_str, 16)
                    callers.setdefault(t, []).append(f["start"])
                except ValueError:
                    pass
            x += i.size
    for f in fl:
        if not (LO <= f["start"] < HI):
            continue
        print(f"=== {f['start']:#x}..{f['limit']:#x} callers={[hex(c) for c in callers.get(f['start'], [])]}", file=out)
        x = f["start"]
        while x < f["limit"]:
            if x in e.labels:
                print(f"{e.labels[x]}:", file=out)
            if x in p.insns:
                i = p.insns[x]
                t = e.insn_text(i) or f"{i.mnemonic} {i.op_str}"
                print(f"  {x:05x}  {t}", file=out)
                x += i.size
            elif x in p.fix_at:
                print(f"  {x:05x}  dd {e.sym(p.fix_at[x][1])}", file=out)
                x += 4
            else:
                print(f"  {x:05x}  db {p.cbytes[x - p.code.base]:02x}", file=out)
                x += 1


if __name__ == "__main__":
    main()
