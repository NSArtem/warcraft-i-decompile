"""Run the wc1.match checks for one C file while other analysts' symbol files
are mid-write.

`python3 -m wc1.match` loads the whole symbol database strictly and stops on
any parse error or duplicate address in analysis/symbols/*.toml (several
analysts share the tree).  This wrapper does the same compile, relocation and
data comparison but loads the database non-strictly, i.e. it uses every entry
it can read and ignores the broken files.  Usage:

    python3 -m wc1.mod_104b0_match <file.c> [--cc ow2|10.0a|other]

The authoritative check is still `python3 -m wc1.match <file.c>` once the tree
is consistent; this is only a development aid for a busy tree.
"""
import argparse
import os
import sys

from . import analysis, match, path, symbols


def run(src, cc):
    outdir = path("build", "mod_104b0", "match")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".obj")
    mod = match.compile_c(src, None, out, cc=cc)
    funcs, datas, errs = symbols.load(strict=False)
    if errs:
        print(f"({len(errs)} symbol-database errors ignored)", file=sys.stderr)
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.run()
    res = match.match_module(p, mod, by_link)
    ok = True
    for name, status, problems in res:
        print(f"{status:9} {name}")
        for pr in problems[:6]:
            print(f"            {pr}")
        ok &= status == "MATCH"
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--cc", choices=("ow2", "10.0a", "other"))
    a = ap.parse_args(argv)
    cc = match.file_cc(a.src)
    if a.cc == "other":
        cc = match.other_cc(cc)
    elif a.cc:
        cc = a.cc
    return run(a.src, cc)


if __name__ == "__main__":
    sys.exit(main())
