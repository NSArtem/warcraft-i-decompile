"""Probe: list incoming interior refs (production emit.replaced_interior_refs) for B1/B2 candidates,
with branch encoding size, and which function owns the source. Read-only."""
from wc1 import analysis, emit, symbols
p = analysis.run(); funcs, _, _ = symbols.load()
by_start = {f["start"]: f for f in p.functions}
starts = sorted(by_start)
import bisect
def owner(a):
    k = bisect.bisect_right(starts, a) - 1; s = starts[k]; e = funcs.get(s)
    return f"{s:#x}:{(e or {}).get('name','?')}:{'C' if (e or {}).get('src') else ('ref' if (e or {}).get('ref') else 'asm')}"
for a in (0x1e380, 0x2315c, 0x23170, 0x2e96c, 0x2efd0, 0x2f73c, 0x157e8):
    f = by_start[a]
    errs = emit.replaced_interior_refs(p, [(f["start"], f["end"])], {a})
    print(f"{a:#x} {funcs[a]['name']} [{f['start']:#x},{f['end']:#x}) limit={f['limit']:#x}")
    for m in errs:
        src = int(m.split()[0], 16); i = p.insns.get(src)
        print("   ", m, "| size", i.size if i else "fixup", "| from", owner(src))
