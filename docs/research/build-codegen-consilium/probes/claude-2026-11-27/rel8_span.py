"""Probe: ASM rel8 branches whose span contains a C cut while both endpoints stay ASM.
Usage (repo root = export of a21772b): python3 rel8_span.py
Reads only: war.exe analysis + symbols DB. Writes nothing."""
import sys
from capstone import x86
from wc1 import analysis, symbols
p = analysis.run()
funcs, datas, _ = symbols.load()
by_start = {f["start"]: f for f in p.functions}
def frange(a):
    f = by_start[a]; return (f["start"], f["end"])
cur = sorted({frange(e["addr"]) for e in funcs.values() if e.get("src") and e["addr"] in by_start})
def spans(cuts):
    cuts = sorted(cuts)
    def inside(a): return any(s <= a < e for s, e in cuts)
    out = []
    for ia, i in p.insns.items():
        if i.size == 2 and (i.mnemonic in analysis.COND_JUMPS or i.mnemonic == "jmp") and i.operands and i.operands[0].type == x86.X86_OP_IMM:
            t = i.operands[0].imm & 0xFFFFFFFF
            if inside(ia) or inside(t): continue
            lo, hi = min(ia, t), max(ia, t)
            hit = [(s, e) for s, e in cuts if lo < s and e <= hi + 1]
            if hit: out.append((ia, t, hit))
    return out
print("current src cuts:", len(cur), "rel8 cross-cut spans:", len(spans(cur)))
cands = {"IntroOpSyncSound": [0x23170], "IntroOpPlaySound": [0x2315c], "Play+Sync": [0x2315c, 0x23170],
         "GroupB Play+Sync+Wait": [0x2315c, 0x23170, 0x231cc], "ApplyScenarioTerrainKindRects": [0x1e380],
         "UnitFinalizeGone": [0x2e96c], "SelectionClickUnit": [0x2efd0], "MissionDefeat": [0x2f73c],
         "ChooseCampaignDialog": [0x157e8]}
for name, addrs in cands.items():
    extra = [frange(a) for a in addrs]
    sp = spans(cur + extra)
    print(f"{name}: +cuts {[(hex(s),hex(e)) for s,e in extra]} -> rel8 cross-cut spans {[(hex(a),hex(t)) for a,t,_ in sp]}")
