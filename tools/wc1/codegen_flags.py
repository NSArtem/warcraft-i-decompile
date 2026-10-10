"""Flag ablation/sweep over the matched samples in src/codegen/.

usage: python3 -m wc1.codegen_flags [--out build/codegen/flags.txt]

Every src/codegen/*.c starts with `codegen-flags: <wcc386 flags>` (the set that
MATCHes all its annotated functions).  For each file this tool
  1. checks the base set (every function must be MATCH),
  2. removes each flag of the base set in turn and reports which functions stop
     matching (= what that flag is needed for),
  3. adds each flag of a catalogue of other switches (optimisation letters,
     CPU models, frame/debug options, struct packing, enum size, FPU) to the
     base set and reports which functions stop matching (= what the switch
     breaks) or newly match.
The report is written to build/codegen/flags.txt; exit status 1 if a base set
does not match (so tests/test_codegen.py can use it).
"""
import argparse
import glob
import os
import re
import sys

from . import codegen_sweep as cs
from . import path

# switches probed on top of each base set (the spelled-out ones of the task)
EXTRA = ("-od -ox -os -oa -ob -oc -oe -of -of+ -oh -oi -ok -om -on -oo -op -or -ou "
         "-3r -5r -6r -zp1 -zp4 -zp8 -ei -fpi -fp3 -d0 -d1 -d1+ -d2 -d3 -oz -zc").split()


def base_flags(src):
    m = re.search(r"codegen-flags:\s*(.*)", open(src).read())
    return m.group(1).strip() if m else None


def status(src, flags):
    t = cs.sweep(src, [flags], quiet=True)[0]
    if t[1] is None:
        return None
    return {n: st for n, a, st, g, w in t[1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=path("build", "codegen", "flags.txt"))
    a = ap.parse_args()
    files = sorted(glob.glob(path("src", "codegen", "*.c")))
    out = []
    ok_all = True
    for src in files:
        base = base_flags(src)
        if base is None:
            continue
        name = os.path.basename(src)
        st = status(src, base)
        good = st is not None and all(v == "MATCH" for v in st.values())
        ok_all &= good
        out.append(f"== {name}  [{base}]  {'ALL MATCH' if good else 'NOT MATCHING: ' + str(st)}")
        if not good:
            continue
        toks = base.split()
        need = []
        for t in toks:
            if t == "-s":
                continue
            s2 = status(src, " ".join(x for x in toks if x != t))
            lost = sorted(n for n, v in (s2 or {}).items() if v != "MATCH") if s2 else ["<compile error>"]
            need.append(f"{t}: " + (", ".join(lost) if lost else "not needed here"))
        out.append("   removing -> breaks: " + "; ".join(need))
        brk = []
        for e in EXTRA:
            if e in toks:
                continue
            # replace a competing switch of the same family instead of just appending
            fam = {"-od": "-ot", "-ox": "-ot", "-os": "-ot", "-3r": "-4r", "-5r": "-4r", "-6r": "-4r",
                   "-zp1": "-zp2", "-zp4": "-zp2", "-zp8": "-zp2"}.get(e)
            cand = [(e if x == fam else x) for x in toks] if fam in toks else toks + [e]
            s2 = status(src, " ".join(cand))
            lost = sorted(n for n, v in (s2 or {}).items() if v != "MATCH") if s2 else ["<compile error>"]
            if lost:
                brk.append(f"{e}->{','.join(lost)}")
        out.append("   adding/swapping breaks: " + ("; ".join(brk) or "nothing"))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write("\n".join(out) + "\n")
    print("\n".join(out))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
