"""Progress towards the project goal (docs/GOAL.md), measured from the symbol
database and code discovery.

Every discovered function is classified:

  scope   out: Miles AIL, hand-written asm (modules.toml kind ail / asm /
               asm-shared), the Watcom runtime (an entry in
               analysis/symbols/clib.toml, or a runtime library table object
               listed in OUT_MODULES);
          in:  everything else (game code and Blizzard's own video/input/
               resource libraries).  A runtime-kind function nobody has
               classified yet stays in scope and is counted as
               "unclassified" until it is named (or moved to clib.toml).
  name    semantic: a DB entry whose name is not an address placeholder
          (fn_1234, dat_..., ...) at confidence verified/high/medium.
  C       T3:  `src =` (wc1.match MATCH, built from C; make verify checks it),
               under the file's declared compiler (codegen-compiler header:
               10.0a or OW2; reported per compiler, counted the same)
          T4:  `ref =` + `ref_verified_by = "difftest: ..."` (the compiled
               reference C was run against the original under wc1.emu)
          ref: `ref =` only (reference C exists, not checked yet)
          none
  done    semantic name and (T3, or T4 with a `t3_blocker`)

usage: python3 -m wc1.progress [--check] [--json] [--todo N] [--kind K]
  --check   exit 1 unless every in-scope function is done (the goal)
  --json    machine-readable summary and per-function rows
  --todo N  list the first N in-scope functions that are not done, with
            what is missing (address order; --kind narrows the list)
"""
import argparse
import bisect
import collections
import json
import re
import sys
import tomllib

from . import analysis, path, symbols

PLACEHOLDER = re.compile(r"^(fn|sub|func|dat|data|mod|unk|loc|nullsub)_[0-9a-fA-F]+(_\w+)?$")
NAMED_CONFIDENCE = ("verified", "high", "medium")
OUT_KINDS = {"ail": "Miles AIL (third-party)", "asm": "hand-written asm",
             "asm-shared": "hand-written asm"}
# Library objects that discovery splits into many "functions" (no source exists).
OUT_MODULES = {"int_stub_table": "Watcom runtime", "cstrtx_begtext": "Watcom runtime"}
CLIB_FILE = "analysis/symbols/clib.toml"


def load_modules(modules_file=None):
    with open(modules_file or path("analysis", "modules.toml"), "rb") as fh:
        return tomllib.load(fh)["module"]


def is_semantic(e):
    return bool(e) and not PLACEHOLDER.match(e["name"]) and e["confidence"] in NAMED_CONFIDENCE


def c_status(e):
    if not e:
        return "none"
    if e.get("src"):
        return "T3"
    if e.get("ref"):
        return "T4" if str(e.get("ref_verified_by", "")).startswith("difftest:") else "ref"
    return "none"


def _src_cc(src):
    """The codegen-compiler of a src file ("ow2" when it has no header or the
    file is absent, e.g. synthetic test rows)."""
    import os
    from . import match
    p = path(src)
    return match.file_cc(p) if os.path.isfile(p) else "ow2"


def classify(starts, funcs_db, modules):
    """One row per discovered function start (pure: tests feed synthetic data)."""
    mstarts = [m["start"] for m in modules]
    rows = []
    for a in sorted(starts):
        i = bisect.bisect_right(mstarts, a) - 1
        m = modules[i] if i >= 0 and a < modules[i]["end"] else {"name": "?", "kind": "?"}
        e = funcs_db.get(a)
        out = None
        if e and e["_file"].replace("\\", "/") == CLIB_FILE:
            out = "Watcom runtime"
        elif m["kind"] in OUT_KINDS:
            out = OUT_KINDS[m["kind"]]
        elif m["name"] in OUT_MODULES:
            out = OUT_MODULES[m["name"]]
        named = is_semantic(e)
        c = c_status(e)
        blocker = bool(e and e.get("t3_blocker"))
        row = {"addr": a, "module": m["name"], "kind": m["kind"], "scope": "out" if out else "in",
               "out_reason": out, "name": e["name"] if e else None, "named": named, "c": c,
               "blocker": blocker,
               "unclassified": out is None and m["kind"] == "runtime" and not named}
        # display only: the compiler the T3 match is proved with (codegen-compiler header)
        row["cc"] = _src_cc(e["src"]) if c == "T3" else None
        row["done"] = out is None and named and (c == "T3" or (c == "T4" and blocker))
        missing = []
        if out is None:
            if not named:
                missing.append("name")
            if c == "none":
                missing.append("C")
            elif c == "ref":
                missing.append("C-vs-original difftest")
            if c in ("ref", "T4") and not blocker:
                missing.append("t3_blocker")
        row["missing"] = missing
        rows.append(row)
    return rows


def summarize(rows):
    inn = [r for r in rows if r["scope"] == "in"]
    s = {
        "functions": len(rows),
        "out_of_scope": dict(collections.Counter(r["out_reason"] for r in rows if r["scope"] == "out")),
        "in_scope": len(inn),
        "in_scope_by_kind": dict(collections.Counter(r["kind"] for r in inn)),
        "unclassified_runtime": sum(r["unclassified"] for r in inn),
        "named": sum(r["named"] for r in inn),
        "c": {k: sum(r["c"] == k for r in inn) for k in ("T3", "T4", "ref", "none")},
        "ref_or_T4_without_blocker": sum(r["c"] in ("ref", "T4") and not r["blocker"] for r in inn),
        "T3_by_compiler": dict(collections.Counter(r.get("cc") or "ow2" for r in inn if r["c"] == "T3")),
        "done": sum(r["done"] for r in inn),
    }
    s["by_kind"] = {}
    for k in sorted(s["in_scope_by_kind"]):
        ks = [r for r in inn if r["kind"] == k]
        s["by_kind"][k] = {"total": len(ks), "named": sum(r["named"] for r in ks),
                           "T3": sum(r["c"] == "T3" for r in ks), "T4": sum(r["c"] == "T4" for r in ks),
                           "ref": sum(r["c"] == "ref" for r in ks), "done": sum(r["done"] for r in ks)}
    return s


def _pct(n, d):
    return f"{100.0 * n / d:5.1f}%" if d else "  n/a"


def report(s):
    n = s["in_scope"]
    out = [f"wc1 progress towards docs/GOAL.md ({s['functions']} discovered functions)", ""]
    out.append(f"out of scope   {s['functions'] - n:5d}   " +
               ", ".join(f"{k} {v}" for k, v in sorted(s["out_of_scope"].items())))
    out.append(f"in scope       {n:5d}   " +
               ", ".join(f"{k} {v}" for k, v in sorted(s["in_scope_by_kind"].items())) +
               f"  (runtime not yet classified: {s['unclassified_runtime']})")
    out += ["", "in scope:",
            f"  semantic name (>= medium)          {s['named']:5d}  {_pct(s['named'], n)}",
            f"  C: T3 matched, built from C        {s['c']['T3']:5d}  {_pct(s['c']['T3'], n)}",
            "        by compiler: " + ", ".join(f"{k} {v}" for k, v in sorted(s.get("T3_by_compiler", {}).items())),
            f"     T4 reference C, difftested      {s['c']['T4']:5d}  {_pct(s['c']['T4'], n)}",
            f"     reference C, not checked yet    {s['c']['ref']:5d}  {_pct(s['c']['ref'], n)}",
            f"     no C                            {s['c']['none']:5d}  {_pct(s['c']['none'], n)}",
            f"  reference C without t3_blocker     {s['ref_or_T4_without_blocker']:5d}",
            f"  DONE (name + T3, or T4 + blocker)  {s['done']:5d}  {_pct(s['done'], n)}",
            "", f"  {'kind':10} {'total':>6} {'named':>6} {'T3':>5} {'T4':>5} {'ref':>5} {'done':>6}"]
    for k, v in s["by_kind"].items():
        out.append(f"  {k:10} {v['total']:6d} {v['named']:6d} {v['T3']:5d} {v['T4']:5d} {v['ref']:5d} {v['done']:6d}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wc1.progress", description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--todo", type=int, default=0, metavar="N")
    ap.add_argument("--kind")
    a = ap.parse_args(argv)
    funcs, _, errors = symbols.load(strict=False)
    if errors:
        print("symbol database has errors (python3 -m wc1.symbols); progress not computed", file=sys.stderr)
        return 2
    rows = classify([f["start"] for f in analysis.run().functions], funcs, load_modules())
    s = summarize(rows)
    if a.json:
        print(json.dumps({"summary": s, "functions": rows}, indent=1))
    else:
        print(report(s))
        if a.todo:
            todo = [r for r in rows if r["scope"] == "in" and not r["done"]
                    and (a.kind is None or r["kind"] == a.kind)]
            print(f"\nnot done ({len(todo)}; first {min(a.todo, len(todo))}):")
            for r in todo[:a.todo]:
                print(f"  {r['addr']:#07x}  {r['module']:18} {r['name'] or '-':28} missing: {', '.join(r['missing'])}")
    if a.check and s["done"] != s["in_scope"]:
        if not a.json:
            print(f"\nGOAL NOT MET: {s['in_scope'] - s['done']} in-scope functions not done")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
