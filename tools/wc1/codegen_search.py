"""Greedy search over wcc386 optimisation switches for the best byte similarity
to the original functions.

usage: python3 -m wc1.codegen_search file.c [file2.c ...] --base "-s -ot" [--pool "a b c ..."]

Each function in the C files carries an `/* @0xADDR */` annotation (see
codegen_sweep).  Starting from --base, repeatedly adds the single switch from
the pool (each switch is passed as `-<sw>`) that increases the mean
SequenceMatcher ratio of (compiled, original) bytes, until no switch helps.
Reports the final score, flag set, and per-function status.  A score of 1.0
for every function means all MATCH.
"""
import argparse
import difflib

from . import codegen_sweep as cs

POOL = ("-oa -ob -oc -oe -of -of+ -oh -oi -ok -ol -ol+ -om -on -oo -op -or -ou -zp1 -zp4 "
        "-3r -4r -5r -6r -ei -zc -zu -fpi -fp3 -d1 -d1+ -d2 -d3 -oi+ -ox -os -ot -od -oz").split()


def score(files, flags):
    tot, n, ok = 0.0, 0, 0
    detail = []
    for f in files:
        t = cs.sweep(f, [flags], quiet=True)
        _, rows, err = t[0]
        if rows is None:
            return -1.0, 0, []
        for name, a, st, got, want in rows:
            r = 1.0 if st == "MATCH" else difflib.SequenceMatcher(None, got, want, autojunk=False).ratio()
            tot += r
            n += 1
            ok += st == "MATCH"
            detail.append((name, a, round(r, 3), st))
    return tot / max(n, 1), ok, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--base", default="-s -ot")
    ap.add_argument("--pool", default=None)
    a = ap.parse_args()
    pool = a.pool.split() if a.pool else POOL
    flags = a.base
    best, ok, detail = score(a.files, flags)
    print(f"start  {best:.4f} ok={ok}  [{flags}]")
    while True:
        cand = None
        for sw in pool:
            if sw in flags.split():
                continue
            s, k, d = score(a.files, flags + " " + sw)
            if s > best + 1e-9 and (cand is None or s > cand[0]):
                cand = (s, k, d, sw)
        if cand is None:
            break
        best, ok, detail, sw = cand
        flags += " " + sw
        print(f"add {sw:6} {best:.4f} ok={ok}  [{flags}]")
    for d in detail:
        print("  ", d)


if __name__ == "__main__":
    main()
