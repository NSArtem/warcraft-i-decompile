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

A single matched function is *not* enough: before an object's extent is
admitted, its **whole code segment** is verified byte-for-byte against
`war.exe` at `[base, base + seglen)`, masking only the object's relocation
fields.  Every library relocation must land on a `war.exe` fixup and no
`war.exe` fixup may sit on an unmasked library byte.  This rejects an object
whose one coincidental function match does not represent the object (review
finding `rev-e8-01`: `cstrtx3r:cstrtx32`'s `__exit_` matched inside
`clib3r:cstrt386`, and the extrapolated extent overlapped `cstrt386`).  Extents
that overlap after verification are removed as a contested set (fail closed),
never resolved by set intersection.

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
from collections import Counter, defaultdict
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


_MODULE_CACHE = {}


def _module_index(root=None):
    """{(lib, module name): Module} for the configured 10.0a libraries."""
    key = str(root or oldcc.root())
    if key not in _MODULE_CACHE:
        _MODULE_CACHE[key] = {(lib, m.name): m for lib, m in clib_sig.load_modules(key)}
    return _MODULE_CACHE[key]


def _extent_mask(seg):
    """1 for every byte covered by one of the object's relocations."""
    mask = bytearray(len(seg.data))
    for f in seg.fixups:
        for k in range(f.offset, min(f.offset + f.size, len(seg.data))):
            mask[k] = 1
    return mask


def verify_segment(prog, seg, base):
    """Full-segment masked verification of one library CODE segment at `base`.

    Every non-relocation byte of the object's code contribution must equal
    `war.exe` at `[base, base + seglen)`; every non-self-relative library
    relocation must land on a `war.exe` fixup, and no `war.exe` fixup may sit
    on an unmasked library byte.  A single matched function therefore cannot
    admit an object whose remaining code differs.

    Returns `(ok, reason, detail)` with JSON-safe values.
    """
    if seg.cls != "CODE" or not seg.data:
        return False, "not a non-empty CODE segment", {}
    if len(seg.data) != seg.length:
        return False, "segment data does not cover its SEGDEF length", {
            "segdef_length": seg.length, "data_length": len(seg.data)}
    n = len(seg.data)
    o0 = base - prog.code.base
    if o0 < 0 or o0 + n > len(prog.cbytes):
        return False, "extent outside the war.exe code object", {"base": base, "size": n}
    mask = _extent_mask(seg)
    bad = [k for k in range(n) if not mask[k] and seg.data[k] != prog.cbytes[o0 + k]]
    if bad:
        return False, "unmasked byte differs from war.exe", {
            "first_offset": bad[0], "mismatched_bytes": len(bad)}
    extra = [k for k in range(n) if not mask[k] and (base + k) in prog.fix_at]
    if extra:
        return False, "war.exe relocation on an unmasked library byte", {
            "first_offset": extra[0], "relocations": len(extra)}
    missing = [f.offset for f in seg.fixups
               if not f.self_rel and (base + f.offset) not in prog.fix_at]
    if missing:
        return False, "library relocation without a war.exe fixup", {
            "first_offset": missing[0], "relocations": len(missing)}
    return True, "full masked segment match", {
        "bytes": n, "relocations": len(seg.fixups), "masked_bytes": sum(mask)}


def verify_extent(prog, lib, module, segi, base, root=None):
    """Re-read one library object from the 10.0a tree and verify its extent.

    Public so the corpus regression tests can verify every admitted extent
    against `war.exe` from scratch rather than trusting the cached sweep.
    """
    mod = _module_index(root).get((lib, module))
    if mod is None:
        return False, "library object not found", {}
    if not 1 <= segi <= len(mod.segments):
        return False, "segment index out of range", {"segments": len(mod.segments)}
    return verify_segment(prog, mod.segments[segi - 1], base)


def _extents(prog, rows):
    """Full-segment-verified, non-overlapping extents plus rejection records."""
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r["lib"], r["module"], r["segi"])].append(r)
    index = _module_index()
    candidates, rejected = {}, []
    for key, rs in sorted(grouped.items()):
        lib, module, segi = key
        bases = {r["addr"] - r["off"] for r in rs}
        rec = {"lib": lib, "module": module, "segi": segi}
        if len(bases) != 1:
            rejected.append(dict(rec, reason="inconsistent base addresses",
                                 bases=sorted(bases)))
            continue
        base = bases.pop()
        mod = index.get((lib, module))
        if mod is None:
            rejected.append(dict(rec, base=base, reason="library object not found"))
            continue
        seg = mod.segments[segi - 1]
        ok, reason, detail = verify_segment(prog, seg, base)
        if not ok:
            rejected.append(dict(rec, base=base, reason=reason, detail=detail))
            continue
        candidates[key] = (base, base + len(seg.data))

    # Fail closed: every extent in an overlapping group is contested and removed.
    # A pair is never labelled from the intersection of overlapping extents.
    ordered = sorted(candidates.items(), key=lambda kv: (kv[1][0], kv[1][1], kv[0]))
    partners = defaultdict(set)
    for i, (ka, (_lo_a, hi_a)) in enumerate(ordered):
        for kb, (lo_b, _hi_b) in ordered[i + 1:]:
            if lo_b >= hi_a:
                break
            partners[ka].add(kb)
            partners[kb].add(ka)
    for key in sorted(partners):
        lo, hi = candidates[key]
        rejected.append({
            "lib": key[0], "module": key[1], "segi": key[2],
            "base": lo, "end": hi, "reason": "overlaps another verified extent",
            "overlaps": sorted("%s:%s" % (k[0], k[1]) for k in partners[key]),
        })
    extents = {k: v for k, v in candidates.items() if k not in partners}
    diag = {
        "inconsistent": [r for r in rejected
                         if r["reason"] == "inconsistent base addresses"],
        "rejected_extents": sorted(
            rejected, key=lambda r: (r.get("base", -1), r["lib"], r["module"],
                                     r["segi"], r["reason"])),
        "rejected_counts": dict(sorted(Counter(r["reason"] for r in rejected).items())),
        "extents_verified": len(candidates),
        "extents_admitted": len(extents),
        "extents_rejected": len(rejected),
        "overlap_conflicts": len(partners),
        "extent_bytes": sum(hi - lo for lo, hi in extents.values()),
    }
    return extents, diag


def libsig_corpus(prog=None, refresh=False, exclude_modules=()):
    """Corpus B1: full-segment-verified library objects only.

    `exclude_modules` is used for the documented `intxa386` sensitivity run;
    the main corpus leaves it empty.  Every admitted extent has passed
    `verify_segment` and no two admitted extents overlap.
    """
    prog = prog or war_program()
    root = oldcc.root()
    rec = _unit_records(prog, root, refresh=refresh)
    if rec.get("missing_libraries"):
        # a 10.0a tree with a library missing still yields a corpus; it is recorded
        pass
    extents, diag = _extents(prog, rec["units"])
    excluded_modules = sorted(set(exclude_modules))
    if excluded_modules:
        extents = {k: v for k, v in extents.items() if k[1] not in excluded_modules}
        diag["extents_admitted"] = len(extents)
        diag["extent_bytes"] = sum(hi - lo for lo, hi in extents.values())
        diag["excluded_modules"] = excluded_modules
    ext = sorted(extents.items(), key=lambda kv: kv[1][0])
    funcs = war_functions(prog)
    owner = {}
    for key, (lo, hi) in extents.items():
        for f in prog.functions:
            if lo <= f["start"] < hi:
                owner[f["start"]] = key
    for f in funcs:
        key = owner.get(f["start"])
        if key is not None:
            f["cu"] = "%s:%s" % (key[0], key[1])
    cus = [{"id": "%s:%s" % (k[0], k[1]), "lib": k[0], "module": k[1], "segi": k[2],
            "start": lo, "end": hi} for k, (lo, hi) in ext]
    labels, excluded = [], defaultdict(int)
    for i in range(1, len(funcs)):
        a, b = funcs[i - 1], funcs[i]
        ka, kb = owner.get(a["start"]), owner.get(b["start"])
        if ka is None or kb is None:
            excluded["function outside every admitted extent"] += 1
            continue
        if ka == kb:
            labels.append({"i": i, "prev": a["start"], "cur": b["start"], "truth": "same_cu",
                           "evidence": ("one full-segment-verified library object covers "
                                        "both: %s:%s" % (ka[0], ka[1]))})
            continue
        # Different objects: only accept when no other module's code sits between.
        prev_end = extents[ka][1]
        if prev_end > b["start"]:
            excluded["overlapping extents"] += 1
            continue
        gap = prog.cbytes[prev_end - prog.code.base:b["start"] - prog.code.base]
        if any(gap) and prog._skip_filler(prev_end, b["start"]) != b["start"]:
            excluded["non-padding bytes between extents"] += 1
            continue
        labels.append({"i": i, "prev": a["start"], "cur": b["start"], "truth": "boundary",
                       "evidence": "%s -> %s" % (ka[0] + ":" + ka[1], kb[0] + ":" + kb[1])})
    same_by_module = Counter()
    for lab in labels:
        if lab["truth"] == "same_cu":
            k = owner[lab["cur"]]
            same_by_module["%s:%s" % (k[0], k[1])] += 1
    dominant = None
    if same_by_module:
        name, n = same_by_module.most_common(1)[0]
        dominant = {"module": name, "same_cu_pairs": n,
                    "share_of_same_cu": n / sum(same_by_module.values()),
                    "share_of_labelled_pairs": n / len(labels)}
    counts = dict(rec["counts"], admitted_extents=len(extents),
                  verified_extents=diag["extents_verified"],
                  rejected_extents=diag["extents_rejected"],
                  excluded_modules=excluded_modules)
    corp = {
        "schema": SCHEMA, "experiment": EXPERIMENT, "id": "libsig",
        "kind": "corpus_b1_real_libsig_object_identity",
        "caveat": ("CU membership is full-segment-verified library object identity from 10.0a "
                   "clib3r.lib / cstrtx3r.obj matches; padding and data signals are not used "
                   "to establish it. Every admitted object's whole CODE segment matches war.exe "
                   "with only relocation fields masked, and no admitted extents overlap."),
        "provenance": {"matcher": "wc1.clib_sig", "library_root": "watcom-10.0a",
                       "war_sha256": rec["war_sha256"], "library_files": rec["key"],
                       "verification": ("full masked CODE segment at [base, base+seglen); "
                                        "library relocations required on war.exe fixups; "
                                        "no war.exe fixup on unmasked bytes; overlapping "
                                        "candidate extents removed (fail closed)")},
        "functions": funcs, "cus": cus, "ranges": ranges(prog), "labels": labels,
        "diagnostics": dict(diag, excluded=dict(sorted(excluded.items())),
                            counts=counts, missing_libraries=rec["missing_libraries"],
                            matched_functions=sum(1 for f in funcs if f["cu"]),
                            same_cu_pairs_by_module=dict(sorted(same_by_module.items())),
                            dominant_extent=dominant),
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
