"""Corpus B: real `war.exe` boundaries established independently of the signals.

Two sub-corpora, both independent of padding/data-staircase inference:

**B1 — `libsig` object identity.**  `wc1.clib_sig` matches whole functions of
`original/watcom/10.0a/lib386/dos/clib3r.lib` (and the 10.0a startup object
`cstrtx3r.obj`) into `war.exe` at byte or instruction level.  A match yields
the function's owning library *object* and its offset inside that object;
because `wlink` lays every object's `_TEXT` contribution down contiguously,
`address - offset` is the object's base and `base + object text size` its end.
Two adjacent functions inside one such extent are the same CU; two functions
in different extents are different CUs.  The conclusion is object identity,
never padding.

**B2 — `setup.exe` provenance transitions.**  `original/install/setup.exe` is a
second 32-bit Watcom program that statically links the same AIL library and the
same Watcom runtime objects.  Under that documented premise (docs/subsystems/
modules.md), a function byte-identical in both programs belongs to a CU that
`setup.exe` links *whole*: a sibling of the same CU would appear in `setup.exe`
too.  So an adjacent (shared, unshared) pair cannot be one CU.  This corpus
therefore yields boundary labels only — it measures detection (recall), not
precision, and its assumption is stated in the artifacts.  Pairs in which
either function is shorter than the identity matcher's minimum are excluded:
`wc1.modules_setup` cannot call such a function identical, so its status is not
evidence about object identity (a cross-check against B1 showed that all 23
B1-contradicting labels were of this kind).

Neither sub-corpus uses `zero16`/`zero4`/`zero2`/data-staircase evidence, and
no exploratory game inference is ever fed back into them.
"""
import os
from collections import defaultdict
from pathlib import Path

from wc1 import analysis, clib_sig, modules_setup, oldcc, path

from . import EXPERIMENT, SCHEMA, SCRATCH, dump_json, sha256_file

CONST_POOL = (0x569d0, 0x58440)     # game+library string pool, docs/subsystems/modules.md
WAR = ("original", "install", "war.exe")
SETUP = ("original", "install", "setup.exe")


def war_path():
    return path(*WAR)


def setup_path():
    return path(*SETUP)


def war_program():
    return analysis.run(war_path())


def war_functions(prog):
    """The production partition, in the shape the signal evaluator wants."""
    out = []
    for f in prog.functions:
        out.append({"start": f["start"], "end": f["end"], "body_end": f["end"],
                    "limit": f["limit"], "name": "fn_%x" % f["start"], "cu": None})
    return out


def ranges(prog):
    return {"const": [[CONST_POOL[0], CONST_POOL[1]]],
            "data": [[prog.data.base, CONST_POOL[0]], [CONST_POOL[1], prog.data.base + prog.data.vsize]]}


def _library_key(root):
    files, missing = clib_sig.library_files(root)
    parts = [f"{lib}:{sha256_file(p)}" for lib, _kind, p in files]
    return parts, missing


# ---------------------------------------------------------------------------
# B1: libsig object identity
# ---------------------------------------------------------------------------
def _unit_records(prog, root, refresh=False):
    key = {"war": sha256_file(war_path()), "libraries": _library_key(root)[0]}
    from . import digest as json_digest
    cache = SCRATCH / "libsig10a.json"
    key_digest = json_digest(key)
    if not refresh and cache.exists():
        rec = __import__("json").loads(cache.read_text(encoding="utf-8"))
        if rec.get("key") == key_digest:
            return rec
    missing = []
    matcher, units, hits = clib_sig.run_matching(prog, root, missing)
    accepted, ext, ambiguous, weak = clib_sig.resolve(hits)
    rows = []
    for u, (addr, level, probs, cons) in accepted.items():
        rows.append({"addr": addr, "lib": u.lib, "module": u.mod.name, "segi": u.segi,
                     "off": u.off, "size": len(u.data), "seglen": len(u.seg.data),
                     "level": level})
    rec = {"key": key_digest, "war_sha256": key["war"], "missing_libraries": missing,
           "units": rows,
           "counts": {"library_units": len(units), "accepted": len(rows),
                      "ambiguous": len(ambiguous), "weak": len(weak),
                      "modules": len({(r["lib"], r["module"], r["segi"]) for r in rows})}}
    dump_json(cache, rec)
    return rec


def _extents(rows):
    """{(lib, module, segi): (base, end)} plus consistency diagnostics."""
    grouped = defaultdict(set)
    for r in rows:
        grouped[(r["lib"], r["module"], r["segi"])].add((r["addr"] - r["off"], r["seglen"]))
    extents, diag = {}, {"inconsistent": [], "conflicting_bases": 0}
    for key, cand in sorted(grouped.items()):
        bases = {b for b, _n in cand}
        if len(bases) != 1:
            diag["inconsistent"].append({"unit": list(key), "bases": sorted(bases)})
            continue
        base = bases.pop()
        seglen = max(n for _b, n in cand)
        extents[key] = (base, base + seglen)
    return extents, diag


def libsig_corpus(prog=None, refresh=False):
    prog = prog or war_program()
    root = oldcc.root()
    rec = _unit_records(prog, root, refresh=refresh)
    if rec.get("missing_libraries"):
        # a 10.0a tree with a library missing still yields a corpus; it is recorded
        pass
    extents, diag = _extents(rec["units"])
    ext = sorted(extents.items(), key=lambda kv: kv[1][0])
    cover = defaultdict(set)
    for key, (lo, hi) in extents.items():
        for f in prog.functions:
            if lo <= f["start"] < hi:
                cover[f["start"]].add(key)
    funcs = war_functions(prog)
    for f in funcs:
        ks = cover.get(f["start"])
        if ks and len(ks) == 1:
            f["cu"] = "%s:%s" % (next(iter(ks))[0], next(iter(ks))[1])
    cus = [{"id": "%s:%s" % (k[0], k[1]), "lib": k[0], "module": k[1], "segi": k[2],
            "start": lo, "end": hi} for k, (lo, hi) in ext]
    labels, excluded = [], defaultdict(int)
    for i in range(1, len(funcs)):
        a, b = funcs[i - 1], funcs[i]
        ka, kb = cover.get(a["start"], set()), cover.get(b["start"], set())
        if not ka or not kb:
            excluded["function outside every matched extent"] += 1
            continue
        same = ka & kb
        if same:
            labels.append({"i": i, "prev": a["start"], "cur": b["start"], "truth": "same_cu",
                           "evidence": "one library object covers both: " +
                                       ", ".join("%s:%s" % (k[0], k[1]) for k in sorted(same))})
            continue
        # different objects: only accept when no other module's code sits between
        prev_end = max(extents[k][1] for k in ka)
        if prev_end > b["start"]:
            excluded["overlapping extents"] += 1
            continue
        gap = prog.cbytes[prev_end - prog.code.base:b["start"] - prog.code.base]
        if any(gap) and prog._skip_filler(prev_end, b["start"]) != b["start"]:
            excluded["non-padding bytes between extents"] += 1
            continue
        labs = sorted(ka) + sorted(kb)
        labels.append({"i": i, "prev": a["start"], "cur": b["start"], "truth": "boundary",
                       "evidence": "%s -> %s" % (", ".join("%s:%s" % (k[0], k[1]) for k in sorted(ka)),
                                                 ", ".join("%s:%s" % (k[0], k[1]) for k in sorted(kb)))})
    corp = {
        "schema": SCHEMA, "experiment": EXPERIMENT, "id": "libsig",
        "kind": "corpus_b1_real_libsig_object_identity",
        "caveat": ("CU membership is library object identity from 10.0a clib3r.lib / cstrtx3r.obj "
                   "matches; padding and data signals are not used to establish it."),
        "provenance": {"matcher": "wc1.clib_sig", "library_root": "watcom-10.0a",
                       "war_sha256": rec["war_sha256"], "library_files": rec["key"]},
        "functions": funcs, "cus": cus, "ranges": ranges(prog), "labels": labels,
        "diagnostics": dict(diag, excluded=dict(sorted(excluded.items())),
                            counts=rec["counts"], missing_libraries=rec["missing_libraries"],
                            matched_functions=sum(1 for f in funcs if f["cu"])),
        "_prog": "war",
    }
    return corp


# ---------------------------------------------------------------------------
# B2: setup.exe provenance transitions
# ---------------------------------------------------------------------------
def setup_corpus(prog=None, refresh=False):
    prog = prog or war_program()
    key = {"war": sha256_file(war_path()), "setup": sha256_file(setup_path())}
    from . import digest as json_digest
    cache = SCRATCH / "setup_shared.json"
    key_digest = json_digest(key)
    rec = None
    if not refresh and cache.exists():
        got = __import__("json").loads(cache.read_text(encoding="utf-8"))
        if got.get("key") == key_digest:
            rec = got
    if rec is None:
        shared, nwar, nsetup = modules_setup.shared()
        rec = {"key": key_digest, "shared": {hex(k): [hex(x) for x in v] for k, v in sorted(shared.items())},
               "war_functions": nwar, "setup_functions": nsetup}
        dump_json(cache, rec)
    shared = {int(k, 16) for k in rec["shared"]}
    funcs = war_functions(prog)
    is_shared = [f["start"] in shared for f in funcs]
    # run length of the shared/unshared status over the partition order
    runlen = [0] * len(funcs)
    i = 0
    while i < len(funcs):
        j = i
        while j + 1 < len(funcs) and is_shared[j + 1] == is_shared[i]:
            j += 1
        for k in range(i, j + 1):
            runlen[k] = j - i + 1
        i = j + 1
    labels, excluded = [], defaultdict(int)
    ident_min = modules_setup.MIN_LEN
    for k in range(1, len(funcs)):
        a, b = k - 1, k
        if is_shared[a] == is_shared[b]:
            continue
        # `modules_setup` never reports a function shorter than its identity
        # minimum as shared, so a short function's "not identical" status is not
        # evidence about its owning object; such a pair is excluded rather than
        # labelled a boundary (the B1 object identity shows why: e.g. the 5-byte
        # clib3r:memalloc jump thunk at 0x401bd was a false B2 boundary before
        # this filter).
        if any(funcs[s]["end"] - funcs[s]["start"] < ident_min for s in (a, b)):
            excluded["function shorter than the setup identity minimum"] += 1
            continue
        shared_side = a if is_shared[a] else b
        if runlen[shared_side] < 2:
            excluded["isolated shared function"] += 1
            continue                    # an isolated byte-coincidence, not a library run
        labels.append({"i": k, "prev": funcs[a]["start"], "cur": funcs[b]["start"],
                       "truth": "boundary",
                       "evidence": ("setup.exe-identical run -> not identical" if is_shared[a]
                                    else "not identical -> setup.exe-identical run")})
    runs = []
    i = 0
    while i < len(funcs):
        if not is_shared[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(funcs) and is_shared[j + 1]:
            j += 1
        if j - i + 1 >= 2:
            runs.append([funcs[i]["start"], funcs[j]["start"], j - i + 1])
        i = j + 1
    return {
        "schema": SCHEMA, "experiment": EXPERIMENT, "id": "setup",
        "kind": "corpus_b2_real_setup_shared_transitions",
        "caveat": ("boundary-only labels from setup.exe cross-binary provenance; assuming "
                   "setup.exe links the same library objects whole, a setup-identical function's "
                   "same-CU sibling would also appear in setup.exe. Pairs in which either side is "
                   "shorter than `wc1.modules_setup`'s identity minimum are excluded: that matcher "
                   "cannot call such a function identical, so its status says nothing about object "
                   "identity. No same-CU labels, so this corpus measures detection, not precision."),
        "provenance": {"matcher": "wc1.modules_setup", "war_sha256": key["war"],
                       "setup_sha256": key["setup"]},
        "functions": funcs, "cus": [], "ranges": ranges(prog), "labels": labels,
        "diagnostics": {"war_functions": rec["war_functions"],
                        "setup_functions": rec["setup_functions"],
                        "war_functions_identical_in_setup": len(shared),
                        "identity_min_length": ident_min,
                        "excluded": dict(sorted(excluded.items())),
                        "shared_runs_ge2": len(runs), "runs": runs},
        "_prog": "war",
    }
