"""Cross references for an address: who calls/jumps to it, which fixups
point at it (and from which function), and what a function calls.

usage: python3 -m wc1.xref <addr-hex|name> [--range N]   (N: also count refs
       into [addr, addr+N), e.g. for structures/arrays)
"""
import argparse
import bisect

from capstone import x86

from . import analysis, symbols
from .func import resolve


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("addr")
    ap.add_argument("--range", type=int, default=1)
    a = ap.parse_args()
    p = analysis.run()
    funcs, datas, _ = symbols.load(strict=False)
    names = {e["addr"]: e["name"] for t in (datas, funcs) for e in t.values()}
    starts = [f["start"] for f in p.functions]

    def where(x):
        if not p.in_code(x):
            return f"data {x:#x}"
        k = bisect.bisect_right(starts, x) - 1
        s = starts[k] if k >= 0 else None
        n = names.get(s, f"fn_{s:05x}") if s is not None else "?"
        return f"{n}+{x - s:#x}" if s is not None else f"{x:#x}"

    t0 = resolve(p, a.addr)
    t1 = t0 + a.range
    print(f"references to {names.get(t0, hex(t0))} [{t0:#x}, {t1:#x}):")
    for ia, i in sorted(p.insns.items()):
        if i.mnemonic in analysis.COND_JUMPS | {"jmp", "call"} and i.operands and \
                i.operands[0].type == x86.X86_OP_IMM:
            t = i.operands[0].imm & 0xFFFFFFFF
            if t0 <= t < t1:
                print(f"  {i.mnemonic:5} from {ia:05x} ({where(ia)})")
    for s, (f, t) in sorted(p.fix_at.items()):
        if t0 <= t < t1:
            ins = p.insns.get(p.owner.get(s)) if s in p.owner else None
            txt = f"{ins.mnemonic} {ins.op_str}" if ins else "pointer data"
            print(f"  ptr   from {s:05x} ({where(s)})  {txt}" + (f"  [+{t - t0}]" if t != t0 else ""))
    f = next((f for f in p.functions if f["start"] == t0), None)
    if f:
        callees = sorted({i.operands[0].imm & 0xFFFFFFFF for ia, i in p.insns.items()
                          if f["start"] <= ia < f["limit"] and i.mnemonic == "call"
                          and i.operands and i.operands[0].type == x86.X86_OP_IMM})
        print("calls:", ", ".join(names.get(c, f"fn_{c:05x}") for c in callees))
        refs = sorted({t for s, (fx, t) in p.fix_at.items() if f["start"] <= s < f["limit"]})
        print("refers to:", ", ".join(names.get(r, f"{r:#x}") for r in refs))


if __name__ == "__main__":
    main()
