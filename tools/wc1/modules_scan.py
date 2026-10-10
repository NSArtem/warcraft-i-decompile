"""Module-boundary scan of war.exe's code object (analysis area: MODULES).

Method (evidence, not a guess):

* The linker emits every object module's `_TEXT` contribution contiguously.
  The game's own modules are PARA (16-byte) aligned: wlink pads between two
  modules with *zero* bytes, whereas the compiler pads between two functions of
  the same module with `nop` / `mov eax,eax` / `lea eax,[eax+0]` (never zero).
  A 16-aligned function start preceded by 1..15 all-zero bytes is therefore a
  module start (rule ``zero16``).  Narrower zero gaps before 2/4-aligned starts
  (hand-written asm, library objects with WORD/DWORD alignment) are the same
  signal at lower confidence (``zero2`` / ``zero4``).
* A 16-aligned start with *no* gap (``none16``) or after in-code data
  (``data16``) is only a *possible* start (the previous module may happen to end
  aligned); these are reported, never used as a boundary.
* The data object is laid out in the same module order (strings of every
  module contiguous in link order); the CONST/string pool 0x569d0..0x58440 is
  used as an independent monotonic cross-check of the boundaries
  (``const_window``).

usage: python3 -m wc1.modules_scan [--json build/modules/scan.json] [--table]
"""
import argparse
import bisect
import collections
import json

from . import analysis, path

CODE_BASE = 0x10000
STR_LO, STR_HI = 0x569d0, 0x58440     # game+library string pool (CONST) in the data object
HAND_ASM_START = 0x3024e              # style boundary, see docs/subsystems/modules.md


def gap_kind(p, prev_end, start):
    g = p.cbytes[prev_end - p.code.base:start - p.code.base]
    if not g:
        return "none", 0
    if not any(g):
        return "zero", len(g)
    if p._skip_filler(prev_end, start) == start:
        return "fill", len(g)
    return "data", len(g)


def rule_of(start, kind, n):
    al = 16 if start % 16 == 0 else 4 if start % 4 == 0 else 2 if start % 2 == 0 else 1
    if kind == "zero":
        return {16: "zero16", 4: "zero4", 2: "zero2"}.get(al, "zero1")
    if al == 16 and kind == "none":
        return "none16"
    if al == 16 and kind == "data":
        return "data16"
    return None


def scan(p=None):
    p = p or analysis.run()
    F = p.functions
    starts = [f["start"] for f in F]
    funcs = []
    for k, f in enumerate(F):
        pe = F[k - 1]["end"] if k else p.code.base
        kind, n = gap_kind(p, pe, f["start"])
        funcs.append({"start": f["start"], "end": f["end"], "gap": n, "gap_kind": kind,
                      "rule": rule_of(f["start"], kind, n) if k else None})
    # data refs per function (fixups in decoded code that point into the data object)
    dref = collections.defaultdict(set)
    for s, (f, t) in p.fix_at.items():
        if p.in_code(s) and s in p.owner and p.data.base <= t < p.data.end:
            dref[starts[bisect.bisect_right(starts, s) - 1]].add(t)
    byt = collections.defaultdict(set)
    for fa, ts in dref.items():
        for t in ts:
            byt[t].add(fa)
    # string-pool items (closed or not): address -> sorted referencing function starts
    pool = {t: sorted(fs) for t, fs in byt.items() if STR_LO <= t < STR_HI}
    return {"starts": starts, "funcs": funcs, "pool": {hex(t): [hex(x) for x in v] for t, v in sorted(pool.items())},
            "code_end": p.code.base + p.code.vsize}


def boundaries(sc, weak=True):
    out = []
    for f in sc["funcs"]:
        r = f["rule"]
        if r in ("zero16",) or (weak and r in ("zero4", "zero2")):
            out.append((f["start"], r, f["gap"]))
    return out


def const_window(sc, lo, hi):
    """Range of string-pool addresses referenced only by functions in [lo, hi)."""
    items = [int(t, 16) for t, fs in sc["pool"].items()
             if all(lo <= int(x, 16) < hi for x in fs)]
    return (min(items), max(items) + 1) if items else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=path("build", "modules", "scan.json"))
    ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    sc = scan()
    import os
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w") as fh:
        json.dump(sc, fh)
    cnt = collections.Counter(f["rule"] for f in sc["funcs"] if f["rule"])
    print("rules:", dict(cnt))
    if a.table:
        for f in sc["funcs"]:
            if f["rule"]:
                print("%05x %-7s gap=%-3d" % (f["start"], f["rule"], f["gap"]))


if __name__ == "__main__":
    main()
