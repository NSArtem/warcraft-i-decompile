"""Flag sweep of the other areas' non-matching reference C against the original.

usage: python3 -m wc1.codegen_refs [--out build/codegen/refs.txt]

Copies src/audio/sound.c, src/graphics/gfx_prim.c and src/resources/war.c to
build/codegen/refs/ with an address annotation injected before each function
definition (address from the symbol database, by name), then compiles every
copy under a catalogue of flag sets and reports per function the best byte
similarity, the flag set that achieves it and whether anything matches.
Shows that none of the reference functions is reachable by flags alone.
"""
import argparse
import difflib
import os
import re

from . import codegen_sweep as cs
from . import path, symbols

REFS = [("src/audio/sound.c", "OD"), ("src/graphics/gfx_prim.c", "DBG"), ("src/resources/war.c", "DBG")]

CATALOGUE = []
for opt in ("-od", "-ot", "-ox", "-os", "-ot -ol"):
    for extra in ("", "-d1+", "-d2", "-of+", "-d1+ -of+"):
        for cpu in ("", "-4r", "-5r"):
            CATALOGUE.append(" ".join(x for x in ("-s", opt, extra, cpu, "-zp2") if x))


def annotate(src, dst, byname):
    out = []
    pending = None
    for line in open(src).read().split("\n"):
        m = re.match(r"^[\w][\w\s\*]*?\b(\w+)\s*\([^;]*$", line)
        if m and m.group(1) in byname and not line.startswith(("extern", "typedef")):
            out.append(f"/* @{byname[m.group(1)]:#x} */")
        out.append(line)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w").write("\n".join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=path("build", "codegen", "refs.txt"))
    a = ap.parse_args()
    funcs, _, _ = symbols.load(strict=False)
    byname = {e["name"]: addr for addr, e in funcs.items()}
    lines = []
    for rel, cls in REFS:
        dst = path("build", "codegen", "refs", os.path.basename(rel))
        annotate(path(rel), dst, byname)
        # the reference files declare externs of the shared headers; give them -i src/include
        table = cs.sweep(dst, CATALOGUE, quiet=True)
        best = {}
        for fl, rows, err in table:
            if rows is None:
                continue
            for name, addr, st, got, want in rows:
                r = 1.0 if st == "MATCH" else difflib.SequenceMatcher(None, got, want, autojunk=False).ratio()
                if name not in best or r > best[name][0]:
                    best[name] = (r, fl, st, addr)
        lines.append(f"== {rel}  (observed original style: {cls})")
        for name, (r, fl, st, addr) in sorted(best.items(), key=lambda kv: kv[1][3]):
            lines.append(f"   {name:<22} {addr:#x}  best similarity {r:.2f}  [{fl}]  {st}")
    open(a.out, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
