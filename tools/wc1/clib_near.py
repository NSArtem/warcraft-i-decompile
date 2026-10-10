"""Fast near-match hints: for each original function in the runtime range, the
best OW2 library units by instruction similarity (hints only, never evidence).

usage: python3 -m wc1.clib_near [--lo 0x30000] [--out build/clib/near.txt]

Per original function: top candidates ranked by 0.6*mnemonic-sequence ratio
(push/pop/mov-reg noise removed) + 0.4*similarity of the set of interesting
immediates (>=0x10, not fixup fields).  Prefilter by mnemonic multiset overlap
so the run takes about a minute.
"""
import argparse
import bisect
import difflib
from collections import Counter

import capstone
from capstone import x86

from . import analysis, clib_sig

NOISE = {"push", "pop", "nop", "pushad", "popad"}


def feats(insns):
    mn, imms = [], set()
    for i in insns:
        if i.mnemonic in NOISE:
            continue
        mn.append(i.mnemonic)
        for op in i.operands:
            if op.type == x86.X86_OP_IMM:
                v = op.imm & 0xffffffff
                if 0x10 <= v < 0x100000 and i.mnemonic not in ("call", "jmp") and not i.mnemonic.startswith("j"):
                    imms.add(v)
    return mn, imms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo", default="0x30000")
    ap.add_argument("--out", default="build/clib/near.txt")
    a = ap.parse_args()
    lo = int(a.lo, 16)
    prog = analysis.run()
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    mods = clib_sig.load_modules()
    units = []
    for lib, m in mods:
        for u in clib_sig.code_units(lib, m):
            if len(u.data) < 12:
                continue
            ins = list(md.disasm(u.data, 0))
            mn, im = feats(ins)
            if len(mn) < 5:
                continue
            units.append((u, mn, im, Counter(mn)))
    out = []
    for f in prog.functions:
        if f["start"] < lo:
            continue
        ins = [prog.insns[x] for x in sorted(prog.insns) if f["start"] <= x < f["limit"]]
        mn, im = feats(ins)
        if len(mn) < 5:
            continue
        c = Counter(mn)
        cand = []
        for u, umn, uim, uc in units:
            if not (0.6 <= len(umn) / len(mn) <= 1.6):
                continue
            inter = sum((c & uc).values())
            if inter / max(len(mn), len(umn)) < 0.6:
                continue
            r = difflib.SequenceMatcher(None, umn, mn, autojunk=False).ratio()
            j = len(im & uim) / len(im | uim) if (im | uim) else 0.5
            cand.append((0.6 * r + 0.4 * j, r, j, u))
        cand.sort(key=lambda t: -t[0])
        out.append((f["start"], f["limit"] - f["start"], cand[:4]))
    with open(a.out, "w") as fh:
        for s, n, cand in out:
            fh.write(f"{s:05x} {n:5d}  " + "  |  ".join(
                f"{u.key} {sc:.2f}(seq {r:.2f} imm {j:.2f})" for sc, r, j, u in cand) + "\n")
    print(f"wrote {a.out}: {len(out)} functions")


if __name__ == "__main__":
    main()
