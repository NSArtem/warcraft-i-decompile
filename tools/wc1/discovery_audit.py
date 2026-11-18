"""Per-function audit of code discovery (one row per discovered start).

usage: python3 -m wc1.discovery_audit [--json build/audit/discovery_audit.json]

Each row records how the start was found (origin), the module range and kind,
the symbol-database name if any, the linear instruction run from the start,
the first address at which its stack balance goes negative (the
`stack_underflow` veto of tools/wc1/analysis.py), implausible/segment-
overridden instructions, whether the last instruction falls through, and the
first few instructions.  Used to audit the discovered set: a data table or a
lifted mid-function block shows up as origin tail/ptr/gap-scan with a stack
underflow or odd instructions.

The audit is a report, not a gate; `make verify` only checks the small
regression set in tests/test_pipeline.py.
"""
import argparse
import bisect
import collections
import json
import os
import tomllib

from . import analysis, path, symbols

TERM = {"ret", "retf", "iret", "iretd", "jmp", "hlt"}
ODD = {"in", "out", "insb", "insd", "outsb", "outsd", "hlt", "arpl", "bound",
       "les", "lds", "lfs", "lgs", "lss", "aaa", "aas", "daa", "das", "aam",
       "aad", "into", "salc", "retf", "iretd", "iret", "ljmp", "lcall",
       "enter", "xlatb", "cmc", "sahf", "lahf", "cli", "sti", "int1", "int3",
       "wait", "fwait", "icebp", "ud2", "clts", "lock"}


def linear(p, f):
    """The contiguous instruction run from the start (as the emitter sees it)."""
    a, out = f["start"], []
    while a < f["limit"] and a in p.insns:
        i = p.insns[a]
        out.append((a, i))
        a += i.size
    return out


def rows_of(p=None, db=None):
    p = p or analysis.run()
    if db is None:
        db, _, _ = symbols.load(strict=False)
    ptr_starts = {t for t, k in p.ptr_targets.items()
                  if t in p.insns and k - {"code-table", "jump-table"}}
    gap = {s for s, k in p.seed_kind.items() if k == "gap-scan"}
    modules = []
    with open(path("analysis", "modules.toml"), "rb") as fh:
        modules = tomllib.load(fh)["module"]
    mst = [m["start"] for m in modules]

    def mod(a):
        return modules[bisect.bisect_right(mst, a) - 1]

    def origin(s):
        if s == p.le.entry:
            return "entry"
        if s in p.call_targets:
            return "call"
        if s in ptr_starts:
            return "ptr"
        if s in gap:
            return "gap-scan"
        return "tail"

    rows = []
    for f in p.functions:
        s = f["start"]
        ins = linear(p, f)
        m = mod(s)
        last = ins[-1][1].mnemonic if ins else None
        falls = bool(ins) and last not in TERM and not last.startswith("ret")
        odd = sorted({i.mnemonic for a, i in ins
                      if i.mnemonic in ODD
                      or any(seg in i.op_str for seg in ("cs:", "ds:", "es:",
                                                         "fs:", "gs:", "ss:"))})
        e = db.get(s) if db else None
        rows.append({
            "start": hex(s), "origin": origin(s), "module": m["name"],
            "kind": m["kind"], "name": e["name"] if e else None,
            "file": e["_file"] if e else None, "ninsns": len(ins),
            "frag": hex(analysis.stack_underflow(s, p.insns, f["limit"]))
                    if analysis.stack_underflow(s, p.insns, f["limit"]) else None,
            "odd": odd, "falls_through": falls,
            "first": " ; ".join(f"{i.mnemonic} {i.op_str}".strip()
                                for a, i in ins[:5]),
        })
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wc1.discovery_audit")
    ap.add_argument("--json", default=path("build", "audit", "discovery_audit.json"))
    a = ap.parse_args(argv)
    rows = rows_of()
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w") as fh:
        json.dump(rows, fh, indent=0)
    print(f"{len(rows)} functions -> {a.json}")
    print("origins:", dict(collections.Counter(r["origin"] for r in rows)))
    print("stack underflow:", sum(r["frag"] is not None for r in rows),
          " odd instructions:", sum(bool(r["odd"]) for r in rows),
          " falls through:", sum(r["falls_through"] for r in rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
