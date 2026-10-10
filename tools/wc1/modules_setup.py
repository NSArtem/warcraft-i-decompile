"""Which functions of war.exe's code are byte-identical to code in setup.exe?

setup.exe (original/install/setup.exe) is a second 32-bit Watcom/DOS4GW program
that statically links the same AIL audio library and the same Watcom runtime
(and a small hand-written asm helper module).  A function of war.exe that
reappears (instruction bytes identical once fixup words and out-of-function
relative branch displacements are masked) in setup.exe is library or shared
code, not game code; runs of such functions delimit library ranges.

usage: python3 -m wc1.modules_setup [--json build/modules/setup_shared.json]
"""
import argparse
import collections
import json
import os

from capstone import x86

from . import analysis, path

MIN_LEN = 12


def normalized(p, f, insns_by_func):
    s, e = f["start"], f["end"]
    base = p.code.base
    b = bytearray(p.cbytes[s - base:e - base])
    for a in range(s, e):
        if a in p.fix_at:
            for k in range(4):
                if a + k < e:
                    b[a + k - s] = 0
    for a in insns_by_func:
        i = p.insns[a]
        m = i.mnemonic
        if m == "call" or m == "jmp" or (m.startswith("j") and m != "jmp"):
            if i.operands and i.operands[0].type == x86.X86_OP_IMM:
                t = i.operands[0].imm & 0xffffffff
                if not (s <= t < e):
                    n = 4 if i.size in (5, 6) else 1
                    for k in range(n):
                        j = a + i.size - 1 - k - s
                        if 0 <= j < len(b):
                            b[j] = 0
    return bytes(b)


def _by_func(p):
    import bisect
    starts = [f["start"] for f in p.functions]
    d = collections.defaultdict(list)
    for a in p.insns:
        d[starts[bisect.bisect_right(starts, a) - 1]].append(a)
    return d


def shared(war=None, setup=None):
    W = analysis.Program(war or path("original", "install", "war.exe")).discover().partition()
    S = analysis.Program(setup or path("original", "install", "setup.exe")).discover().partition()
    wb, sb = _by_func(W), _by_func(S)
    wh = collections.defaultdict(list)
    for f in W.functions:
        n = normalized(W, f, wb[f["start"]])
        if len(n) >= MIN_LEN:
            wh[n].append(f["start"])
    out = {}
    for f in S.functions:
        n = normalized(S, f, sb[f["start"]])
        for w in wh.get(n, ()):
            out.setdefault(w, []).append(f["start"])
    return out, len(W.functions), len(S.functions)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=path("build", "modules", "setup_shared.json"))
    a = ap.parse_args()
    sh, nw, ns = shared()
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w") as fh:
        json.dump({hex(k): [hex(x) for x in v] for k, v in sorted(sh.items())}, fh)
    print("war functions %d, setup functions %d, war functions found in setup: %d" % (nw, ns, len(sh)))


if __name__ == "__main__":
    main()
