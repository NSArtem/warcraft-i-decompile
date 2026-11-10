"""Dump symbolic disassembly of every function in 0x13f60..0x19b80 (one process).
usage: python3 -m wc1.game_13f60_dump OUTFILE"""
import sys
from . import analysis, emit, symbols

LO, HI = 0x13f60, 0x19b80


def main():
    p = analysis.run()
    funcs, datas, _ = symbols.load(strict=False)
    names = {e["addr"]: e["link_name"] for t in (datas, funcs) for e in t.values()}
    e = emit.Emitter(p, names=names)
    out = open(sys.argv[1], "w")
    for f in p.functions:
        if not LO <= f["start"] < HI:
            continue
        out.write(f"; function {f['start']:#x}..{f['limit']:#x}\n")
        x = f["start"]
        while x < f["limit"]:
            if x in e.labels:
                out.write(f"{e.labels[x]}:\n")
            if x in p.insns:
                i = p.insns[x]
                out.write(f"  {x:05x}  {e.insn_text(i) or i.mnemonic + ' ' + i.op_str}\n")
                x += i.size
            elif x in p.fix_at:
                out.write(f"  {x:05x}  dd {e.sym(p.fix_at[x][1])}\n")
                x += 4
            else:
                out.write(f"  {x:05x}  db {p.cbytes[x - p.code.base]:02x}\n")
                x += 1
        out.write("\n")


if __name__ == "__main__":
    main()
