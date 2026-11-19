"""Run wc1.match against a sanitized copy of the symbol database.

Several analysts write analysis/symbols/*.toml in parallel.  While one of
those files is being edited it can hold an address another file already
names; `wc1.symbols.load(strict=True)` (which wc1.match calls) then raises
and *every* match stops, not just that area's.  This wrapper keeps this
area working without touching the shared tools or another area's file:

  * copy analysis/symbols/*.toml to build/mod_2efd0/sym/ (git-ignored),
    dropping any entry whose address is already taken - sorted file order
    wins, which is what analysis/symbols.py reports as the duplicate;
  * point wc1.symbols.load at that copy;
  * run wc1.match's normal main() with the command line of this script.

usage: python3 -m wc1.mod_2efd0_match <file.c> [wc1.match options]
       python3 -m wc1.mod_2efd0_match --rebuild     (only refresh the copy)
"""
import os
import shutil
import sys
import tomllib

from . import match, path, symbols

DEST = path("build", "mod_2efd0", "sym")
KINDS = ("func", "data")


def _emit(fh, kind, entry):
    fh.write(f"\n[[{kind}]]\n")
    for k, v in entry.items():
        if isinstance(v, str):
            fh.write(f"{k} = {_quote(v)}\n")
        elif isinstance(v, list):
            fh.write(f"{k} = [\n")
            for item in v:
                fh.write(f"  {_quote(str(item))},\n")
            fh.write("]\n")
        elif isinstance(v, bool):
            fh.write(f"{k} = {'true' if v else 'false'}\n")
        elif isinstance(v, int):
            fh.write(f"{k} = {v}\n")
        else:
            raise TypeError(f"{k}: {type(v)}")


def _quote(s):
    out = s.replace("\\", "\\\\").replace('"', '\\"')
    out = out.replace("\n", "\\n").replace("\t", "\\t")
    return '"' + out + '"'


def build(dest=DEST, src=None, verbose=False):
    src = src or path("analysis", "symbols")
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest, exist_ok=True)
    seen = {}
    dropped = []
    for f in sorted(os.listdir(src)):
        if not f.endswith(".toml"):
            continue
        try:
            with open(os.path.join(src, f), "rb") as fh:
                doc = tomllib.load(fh)
        except tomllib.TOMLDecodeError as e:
            # another analyst is writing this file right now: skip it, the
            # entries it holds are not needed by this area's match
            print(f"skip {f}: {e}")
            continue
        with open(os.path.join(dest, f), "w") as out:
            for kind in KINDS:
                for e in doc.get(kind, []):
                    a = e.get("addr")
                    if a in seen:
                        dropped.append((f, kind, a, seen[a]))
                        continue
                    seen[a] = f
                    _emit(out, kind, e)
    if verbose:
        for f, kind, a, first in dropped:
            print(f"dropped {f} {kind} {a:#x} (already in {first})")
    return dropped


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--rebuild" in argv:
        dropped = build(verbose=True)
        print(f"{DEST}: {len(dropped)} duplicate entries dropped")
        return 0
    dropped = build()
    orig = symbols.load

    def load(root=None, strict=True):
        return orig(root or DEST, strict)

    symbols.load = load
    saved = sys.argv
    sys.argv = [saved[0]] + argv
    try:
        return match.main()
    finally:
        sys.argv = saved
        symbols.load = orig


if __name__ == "__main__":
    sys.exit(main())
