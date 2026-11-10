"""Cross-reference tables for the 0x13f60..0x19b80 range (one process).
usage: python3 -m wc1.game_13f60_xref OUTFILE
For each function: callers/jumpers/pointer refs.  Then each data address
referenced from the range with its lowest-addressed code reference
(ownership rule) and total reference count."""
import sys
import bisect
from collections import defaultdict
from capstone import x86
from . import analysis, symbols

LO, HI = 0x13f60, 0x19b80


def main():
    p = analysis.run()
    funcs, datas, _ = symbols.load(strict=False)
    names = {e["addr"]: e["name"] for t in (datas, funcs) for e in t.values()}
    starts = [f["start"] for f in p.functions]

    def where(x):
        k = bisect.bisect_right(starts, x) - 1
        s = starts[k]
        return f"{names.get(s, 'fn_%05x' % s)}+{x - s:#x}"

    callers = defaultdict(list)
    for ia, i in sorted(p.insns.items()):
        if i.mnemonic in analysis.COND_JUMPS | {"jmp", "call"} and i.operands and \
                i.operands[0].type == x86.X86_OP_IMM:
            t = i.operands[0].imm & 0xFFFFFFFF
            callers[t].append((ia, i.mnemonic))
    ptr = defaultdict(list)
    dref = defaultdict(list)
    for s, (f, t) in sorted(p.fix_at.items()):
        if p.in_code(t):
            ptr[t].append(s)
        else:
            dref[t].append(s)
    out = open(sys.argv[1], "w")
    for f in p.functions:
        a = f["start"]
        if not LO <= a < HI:
            continue
        cs = [f"{ia:05x}" + ("" if m == "call" else "(" + m + ")") for ia, m in callers[a]]
        ps = [f"{s:05x}" for s in ptr[a]]
        out.write(f"{a:05x} {names.get(a, '')} callers={cs} ptrs={ps}\n")
    out.write("\n== data ==\n")
    for t in sorted(dref):
        refs = dref[t]
        mine = [s for s in refs if LO <= s < HI]
        if not mine:
            continue
        low = min(refs)
        own = "OWN" if LO <= low < HI else "OTHER(low=%05x)" % low
        out.write(f"{t:05x} {names.get(t, ''):20} {own} nref={len(refs)} first_in_range={min(mine):05x} nmine={len(mine)}\n")


if __name__ == "__main__":
    main()
