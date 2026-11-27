"""Probe: given the src= set, list every ASM 2-byte rel branch whose target lies in a different
link object (inside a C cut, incl. its entry, or another ASM piece across a cut). Read-only; prints CSV addrs."""
from capstone import x86
from wc1 import analysis, symbols
import bisect
p = analysis.run(); funcs, _, _ = symbols.load()
by_start = {f["start"]: f for f in p.functions}
cuts = sorted({(by_start[e["addr"]]["start"], by_start[e["addr"]]["end"]) for e in funcs.values() if e.get("src") and e["addr"] in by_start})
# merge adjacent cuts from same object is irrelevant for piece identity: piece = maximal asm run between cuts
bounds = []
for s, e in cuts: bounds += [s, e]
def obj_id(a):
    for k, (s, e) in enumerate(cuts):
        if s <= a < e: return ("C", k)
    k = bisect.bisect_right([s for s, _ in cuts], a)
    return ("ASM", k)
out = []
for ia, i in p.insns.items():
    if i.size == 2 and i.operands and i.operands[0].type == x86.X86_OP_IMM and (i.mnemonic in analysis.COND_JUMPS or i.mnemonic == "jmp"):
        t = i.operands[0].imm & 0xFFFFFFFF
        a, b = obj_id(ia), obj_id(t)
        if a[0] == "ASM" and a != b:
            out.append(ia)
print(",".join(hex(x) for x in sorted(out)))
