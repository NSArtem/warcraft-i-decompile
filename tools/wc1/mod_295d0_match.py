"""Run the wc1.match checks for one mod_295d0 C file while other analysts'
symbol files are mid-write.

`python3 -m wc1.match` loads the whole symbol database strictly and stops on
any parse error, duplicate address or unknown calling convention in
analysis/symbols/*.toml (several analysts share the tree).  This wrapper does
the same compile, relocation and data comparison with a lenient load: it reads
every file it can, skips entries it cannot use and reports how many it
skipped.  Usage:

    python3 -m wc1.mod_295d0_match <file.c> [--cc ow2|10.0a|other]

The authoritative check is `python3 -m wc1.match <file.c>` once the tree is
consistent; this is a development aid only (same shape as
wc1.mod_104b0_match).
"""
import argparse
import glob
import os
import sys
import tomllib

from . import analysis, match, path, symbols


def load_lenient():
    """symbols.load(strict=False) without the hard failure on a foreign entry
    the shared loader cannot classify (e.g. conv = "interrupt" mid-write)."""
    funcs, datas, skipped = {}, {}, 0
    for f in sorted(glob.glob(path("analysis", "symbols", "*.toml"))):
        try:
            with open(f, "rb") as fh:
                doc = tomllib.load(fh)
        except tomllib.TOMLDecodeError:
            skipped += 1
            continue
        for kind, table in (("func", funcs), ("data", datas)):
            for e in doc.get(kind, []):
                e = dict(e)
                if not isinstance(e.get("addr"), int) or "name" not in e:
                    skipped += 1
                    continue
                conv = e.get("conv", "watcall")
                if kind == "func" and conv not in ("watcall", "cdecl", "asm", "pascal"):
                    skipped += 1
                    continue
                try:
                    ln = symbols.link_name(kind, e)
                except KeyError:
                    skipped += 1
                    continue
                e["link_name"] = ln
                e["_kind"] = kind
                table.setdefault(e["addr"], e)
    return funcs, datas, skipped


def run(src, cc):
    outdir = path("build", "mod_295d0", "match")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".obj")
    mod = match.compile_c(src, None, out, cc=cc)
    funcs, datas, skipped = load_lenient()
    if skipped:
        print(f"({skipped} symbol entries skipped)", file=sys.stderr)
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.run()
    res = match.match_module(p, mod, by_link)
    ok = True
    for name, status, problems in res:
        print(f"{status:9} {name}")
        for pr in problems[:8]:
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
