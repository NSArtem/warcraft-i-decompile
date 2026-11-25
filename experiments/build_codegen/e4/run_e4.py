"""Reproduce E4 with the real toolchain; write the deterministic results file.

    python3 -m experiments.build_codegen.e4.run_e4

Every case either extracts a verified slice and proves binary equivalence, or
is rejected fail-closed with one of the RFC section 6.2 reasons.  The results
file contains no checkout paths, timestamps or host-specific fields: object
digests are canonical SHA-256 over the *loadable* OMF content (see
`omf_extract.loadable_digest`), and compiled/extracted object bytes stay under
`build/e4/`.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

from wc1 import analysis, build, match, oldcc, omf, path, symbols
from experiments.build_codegen.e0 import matcher_proto as e0
from experiments.build_codegen.e0.matcher_proto import OriginalIndex
from experiments.build_codegen.e3.partial_matcher import (
    CandidateRegion, VerifiedRegion, evaluate_module, evaluate_region,
)
from experiments.build_codegen.e4 import fixtures
from experiments.build_codegen.e4 import omf_extract as x
from experiments.build_codegen.e4.fixtures import support
from experiments.build_codegen.e5 import build_e5 as b

ROOT = Path(path())
RESULTS = ROOT / "docs/research/build-codegen/results/e4/results.json"
BASELINE = "ed21ca38feadcadf7e5ba62feed65430d957a6af"
PRODUCTION_PATHS = ("tools/wc1", "src", "analysis", "tests", "asm", "Makefile",
                    "flake.nix", "AGENTS.md")
LE_FIXUPS = 8770
SCORE = ("experiments/build_codegen/e3/fixtures/score_reference.c",
         "-s -ot -ol -4r -zp2", "ScoreTickIncome_", 0, 0x50, 0x24E90)
FARM = ("src/status/panel_state_reference.c",
        "-s -ot -oa -ol -4r -zp2", "FarmPanelChanged_", 0x80, 0xC4, 0x28254)
DIALOG = ("src/mod_16390/dialog_hit_test_reference.c", "-s -os -ol -4r -zp2")

E4_OUT = Path(path("build", "e4", "ba"))
_BASELINE = {}


def digest(data):
    return sha256(bytes(data)).hexdigest()


def inputs():
    p = analysis.run(cache=False)
    funcs, datas, _ = symbols.load()
    db = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    return p, funcs, datas, db


def baseline(p, funcs, db):
    """Compile and verify every existing T3 object once per process.

    E5's own helper names the objects after their source paths, which can push
    a compiler-facing path past Watcom 10.0a's fixed-buffer limit from a deep
    checkout (the rev-e5-01 crash).  E4 uses the same proven placement and
    verification steps with short sequential names.
    """
    if "objects" not in _BASELINE:
        by_src = {}
        for entry in funcs.values():
            if entry.get("src"):
                by_src.setdefault(entry["src"], []).append(entry)
        index = e0.OriginalIndex(p)

        def job(item):
            k, (src, entries) = item
            obj = b.compile_source(src, f"b{k:03d}")
            mod = omf.parse_object(obj)
            cr, _ = build.place(p, src, str(obj), entries)
            results = match.match_module(p, mod, db)
            if not all(r[1] == "MATCH" for r in results):
                raise RuntimeError(f"baseline code mismatch {src}: {results}")
            bases = b.data_bases(p, mod, db, cr[0], index)
            return dict(src=src, obj=obj, cr=cr, funcs=entries, bases=bases,
                        compiler=match.file_cc(str(ROOT / src)),
                        flags=match.file_cflags(str(ROOT / src)))

        with ThreadPoolExecutor(min(8, os.cpu_count() or 1)) as pool:
            _BASELINE["objects"] = sorted(
                pool.map(job, enumerate(sorted(by_src.items()))), key=lambda x: x["cr"])
    return _BASELINE["objects"]


def build_a(p, funcs, datas, db, objects, item, name):
    result = b.link(p, funcs, datas, db, objects + [item], name)
    assert result["identical"], result["comparison"]
    assert result["byte_diffs"] == 0
    assert result["original_fixups"] == result["linked_fixups"] == LE_FIXUPS
    assert result["only_original"] == result["only_linked"] == 0
    return dict(identical=True, byte_diffs=result["byte_diffs"],
                original_fixups=result["original_fixups"],
                linked_fixups=result["linked_fixups"],
                only_original=result["only_original"],
                only_linked=result["only_linked"],
                c_functions=result["c_functions"], c_objects=result["c_objects"],
                comparison="IDENTICAL (loaded image, entry, stack, fixups)")


def extract_real(p, db, index, case):
    src, flags, public, lo, hi, base = case
    obj = fixtures.compile_reference(src, flags, public.rstrip("_").lower())
    mod = omf.parse_object(obj)
    candidate = CandidateRegion(lo, hi, base)
    evaluation = evaluate_region(p, mod, db, candidate, index=index)
    assert isinstance(evaluation.proof, VerifiedRegion), evaluation.result.findings
    proof = evaluation.proof
    packed, provenance = x.extract(obj, evaluation, db, p, index=index)
    final, data_proof = x.apply_data_plan(packed, p, db, {})
    return dict(obj=obj, mod=mod, evaluation=evaluation, proof=proof,
                packed=packed, provenance=provenance, final=final,
                data_proof=data_proof)


def positive_thread(case, p, db, index, objects, funcs, datas, name, description):
    got = extract_real(p, db, index, case)
    obj = support.write_obj(name + "_slice", got["final"])
    item = dict(src=name, obj=obj, cr=(got["provenance"]["orig_start"],
                                      got["provenance"]["orig_end"]),
                funcs=[db[case[2]]], bases={}, experiment=True,
                compiler="10.0a", flags=case[1])
    link = build_a(p, funcs, datas, db, objects, item, name)
    prov = got["provenance"]
    return dict(
        id=name, description=description, source=case[0], compiler="Watcom 10.0a",
        cflags=case[1], function=case[2],
        region=dict(obj_lo=prov["obj_lo"], obj_hi=prov["obj_hi"],
                    orig_start=prov["orig_start"], orig_end=prov["orig_end"],
                    verdict="REGION_MATCH", evidence_digest=prov["evidence_digest"],
                    function_verdict=got["evaluation"].functions[case[2]],
                    compiled_slice_sha256=prov["compiled_slice_sha256"],
                    source_object_loadable_sha256=prov["source_object_loadable_sha256"],
                    extracted_object_loadable_sha256=prov["extracted_object_loadable_sha256"],
                    extracted_object_bytes=prov["extracted_object_bytes"],
                    invariants=prov["invariants"], chunks=prov["chunks"]),
        relocations=dict(transforms=prov["transforms"], added_extdefs=prov["added_extdefs"],
                         dropped=prov["dropped"], branches=len(prov["branches"]),
                         instructions=prov["instructions"],
                         normalization=prov["record_normalization"],
                         data_plan=dict(anchors=got["data_proof"]["anchors"],
                                        scopes=[p_["data_scope"]
                                                for p_ in got["data_proof"]["data_proofs"]])),
        build_a=link)


def controlled_case():
    case = fixtures.controlled()
    evaluation = evaluate_region(case["prog"], case["mod"], case["db"],
                                 case["candidate"], index=case["index"])
    assert isinstance(evaluation.proof, VerifiedRegion), evaluation.result.findings
    proof = evaluation.proof
    text = case["text"]
    seg_fix = next(f for f in case["mod"].segments[0].fixups
                   if f.offset < proof.candidate.obj_hi and f.target_kind == "seg")
    inline = int.from_bytes(text[seg_fix.offset:seg_fix.offset + 4], "little", signed=True)
    const_base = case["prog"].fix_at[case["code_base"] + seg_fix.offset][1] - inline
    packed, provenance = x.extract(case["obj"], evaluation, case["db"], case["prog"],
                                   anchored_segments={case["const_si"]},
                                   index=case["index"])
    final, data_proof = x.apply_data_plan(packed, case["prog"], case["db"],
                                         {case["const_si"]: const_base})
    slice_obj = support.write_obj("p3_slice", final)
    anchor = f"wc1_anchor_{const_base:05x}"
    remainder = support.write_obj(
        "p3_remainder",
        support.remainder_object(case["obj"], provenance["obj_hi"],
                                 extra_publics=[(anchor, case["const_si"], 0)]))
    rebuilt_exe, _ = support.mini_link([slice_obj, remainder, case["runtime"]],
                                      "p3_rebuilt")
    identical, comparison = support.compare(case["oracle_exe"], rebuilt_exe)
    assert identical, comparison
    mod = omf.parse_module(final)[0]
    return dict(
        id="positive_3_const_and_intra_tu_call",
        description="extract A from a real 10.0a [A, B, C] TU; C is a "
                    "cross-neighbour EXTDEF call and the literal is anchored "
                    "through the E5 Fix B3 wc1_anchor_* data mechanism",
        source="experiments/build_codegen/e4/fixtures/controlled_tu.c",
        compiler="Watcom 10.0a", cflags=support.FLAGS,
        layout=dict(text_length=len(text), functions=[[n, a - case["code_base"],
                                                       e - case["code_base"]]
                                                      for n, a, e in case["ranges"]],
                    extracted=[provenance["obj_lo"], provenance["obj_hi"]]),
        anchor=dict(symbol=anchor, address=const_base, literal_size=case["mod"].seg("CONST")[1].length),
        extraction=dict(chunks=provenance["chunks"], invariants=provenance["invariants"],
                        compiled_slice_sha256=provenance["compiled_slice_sha256"],
                        source_object_loadable_sha256=provenance["source_object_loadable_sha256"],
                        extracted_object_loadable_sha256=provenance["extracted_object_loadable_sha256"]),
        transforms=provenance["transforms"],
        slice_externs=mod.externs,
        slice_fixups=[[f.offset, f.self_rel, f.target_kind, f.target]
                      for f in mod.segments[0].fixups],
        data_plan=dict(anchors=data_proof["anchors"],
                       scopes=[p_["data_scope"] for p_ in data_proof["data_proofs"]]),
        oracle=dict(identical=identical, comparison=comparison))


def direct_case():
    case = fixtures.direct_call()
    evaluation = evaluate_region(case["prog"], case["mod"], case["db"],
                                 case["candidate"], index=case["index"])
    assert isinstance(evaluation.proof, VerifiedRegion), evaluation.result.findings
    packed, provenance = x.extract(case["obj"], evaluation, case["db"], case["prog"],
                                   index=case["index"])
    slice_obj = support.write_obj("p3b_slice", packed)
    remainder = support.write_obj(
        "p3b_remainder",
        support.remainder_object(case["obj"], provenance["obj_hi"]))
    rebuilt_exe, _ = support.mini_link([slice_obj, remainder, case["runtime"]],
                                      "p3b_rebuilt")
    identical, comparison = support.compare(case["oracle_exe"], rebuilt_exe)
    assert identical, comparison
    mod = omf.parse_module(packed)[0]
    call, = provenance["direct_calls"]
    return dict(
        id="positive_3b_direct_unfixed_rel32",
        description="NASM TU with a plain (unfixed) intra-TU call rel32 whose "
                    "target is recovered from the module symbol table, converted "
                    "to EXTDEF + self-relative FIXUPP32",
        source="experiments/build_codegen/e4/fixtures/direct_call.asm",
        compiler="NASM 3.x OMF32", cflags="-O0 -f obj",
        call=dict(offset=call["offset"], symbol=call["symbol"],
                  target_object_offset=call["target_object_offset"],
                  target_address=call["target_address"],
                  inline_before=provenance["transforms"][0]["inline_before"],
                  inline_after=provenance["transforms"][0]["inline_after"]),
        added_extdefs=provenance["added_extdefs"],
        transforms=provenance["transforms"],
        slice_text=bytes(mod.segments[0].data).hex(),
        slice_fixups=[[f.offset, f.self_rel, f.target_kind, f.target]
                      for f in mod.segments[0].fixups],
        extraction=dict(chunks=provenance["chunks"], invariants=provenance["invariants"],
                        compiled_slice_sha256=provenance["compiled_slice_sha256"],
                        extracted_object_loadable_sha256=provenance["extracted_object_loadable_sha256"]),
        oracle=dict(identical=identical, comparison=comparison))


def chunk_case():
    case = fixtures.long_chunk()
    evaluation = evaluate_region(case["prog"], case["mod"], case["db"],
                                 case["candidate"])
    assert isinstance(evaluation.proof, VerifiedRegion), evaluation.result.findings
    packed, provenance = x.extract(case["obj"], evaluation, case["db"], case["prog"])
    slice_obj = support.write_obj("p4_slice", packed)
    rebuilt_exe, _ = support.mini_link([slice_obj, case["provider"]], "p4_rebuilt")
    identical, comparison = support.compare(case["oracle_exe"], rebuilt_exe)
    assert identical, comparison
    chunks = provenance["chunks"]
    field = case["field"]
    assert max(c["size"] for c in chunks) <= x.CHUNK
    # No LEDATA32 boundary may fall strictly inside the 4-byte field.
    for chunk in chunks[:-1]:
        end = chunk["object_offset"] + chunk["size"]
        assert not (field < end < field + 4), (chunk, field)
    field_chunk = next(c for c in chunks
                       if c["object_offset"] <= field and
                       field + 4 <= c["object_offset"] + c["size"])
    assert field - field_chunk["object_offset"] <= 1020
    return dict(
        id="positive_4_multi_chunk_ledata",
        description="1500-byte function in one LEDATA with a 4-byte off32 field "
                    "straddling bytes 1022-1026; the extractor splits LEDATA32 "
                    "before the field and wlink still links an identical image",
        text_length=1500, field_offset=case["field"],
        chunks=chunks, chunk_count=len(chunks),
        field_chunk=field_chunk,
        invariants=provenance["invariants"],
        extracted_object_loadable_sha256=provenance["extracted_object_loadable_sha256"],
        oracle=dict(identical=identical, comparison=comparison))


def failure(name, description, case, spec, expected, *, anchored=(), db=None,
            plan=None, evidence=None):
    reason, message, record = None, None, None
    try:
        packed, provenance = x.extract(case["obj"], spec, db or case["db"],
                                       case["prog"], anchored_segments=anchored,
                                       index=case.get("index"))
        if plan is not None:
            x.apply_data_plan(packed, case["prog"], db or case["db"], plan,
                              per_symbol=case.get("per_symbol"))
    except x.UnsupportedExtractionError as exc:
        reason, message, record = exc.reason, exc.record["message"], exc.record
    if reason != expected:
        raise AssertionError(f"{name}: expected {expected}, got {reason}: {message}")
    return dict(id=name, description=description, expected_reason=expected,
                reason=reason, message=message,
                fail_closed=True, evidence=evidence or {})


def negatives(p, db, index):
    out = []
    dialog_obj = fixtures.compile_reference(*DIALOG, "dialog_hit_test")
    dialog = omf.parse_object(dialog_obj)
    by_entry, _, _ = evaluate_module(p, dialog, db, index=index)
    for fn in ("DialogHighlightOn_", "DialogHighlightOff_"):
        evaluation = by_entry[fn]
        case = dict(obj=dialog_obj, prog=p, db=db)
        out.append(failure(
            "N1_" + ("on" if fn.endswith("On_") else "off"), 
            "real folded DialogHighlight" + ("On" if fn.endswith("On_") else "Off") +
            " slice with an outgoing rel8 into DialogItemHitTest's epilogue",
            case, evaluation, x.OUTGOING_REL8,
            evidence=dict(candidate=dict(obj_lo=evaluation.candidate.obj_lo,
                                         obj_hi=evaluation.candidate.obj_hi,
                                         orig_start=evaluation.candidate.orig_start),
                          region_verdict=evaluation.result.verdict,
                          finding_codes=sorted({f["code"] for f in evaluation.result.findings}),
                          rel8=[[r["offset"], r.get("object_target"), r.get("original_target")]
                                for r in evaluation.outgoing_refs
                                if r.get("encoding") == "rel8"])))
    case = fixtures.interior_call()
    out.append(failure(
        "N2_interior_target",
        "direct call rel32 into the neighbour's interior instruction",
        case, evaluate_region(case["prog"], case["mod"], case["db"], case["candidate"]),
        x.INTERIOR_TARGET,
        evidence=dict(call_site=case["candidate"].obj_lo,
                      original_target=case["prog"].functions[1]["start"] + 1)))
    farm = extract_real(p, db, index, FARM)
    reduced = {k: v for k, v in db.items() if k != "UnitPanelStateChanged_"}
    out.append(failure(
        "N3_unknown_symbol_from_war_exe",
        "sibling call whose target exists only in war.exe, not in the symbol "
        "database: identity is never inferred from the original binary",
        dict(obj=farm["obj"], prog=p, db=reduced), farm["evaluation"], x.AMBIGUOUS_SYMBOL,
        db=reduced,
        evidence=dict(sibling="UnitPanelStateChanged_",
                      simplest_guess=db["UnitPanelStateChanged_"]["addr"],
                      database_entry_removed=True)))
    case = fixtures.mutable_data()
    evaluation = evaluate_region(case["prog"], case["mod"], case["db"],
                                 case["candidate"], boundaries=case["boundaries"])
    assert isinstance(evaluation.proof, VerifiedRegion), evaluation.result.findings
    out.append(failure(
        "N4_unproven_mutable_layout",
        "mutable _DATA referenced by the slice without an independently proven base",
        case, evaluation, x.DATA_LAYOUT_MISMATCH, anchored=()))
    another = fixtures.mutable_data()
    evaluation = evaluate_region(another["prog"], another["mod"], another["db"],
                                 another["candidate"], boundaries=another["boundaries"])
    out.append(failure(
        "N4_misanchored_mutable_layout",
        "the same slice with a data plan anchored one object past the real base",
        another, evaluation, x.DATA_LAYOUT_MISMATCH, anchored={2},
        plan={2: case["data_base"] + 4}))
    score = extract_real(p, db, index, SCORE)
    mutated = fixtures.swap_extname(score["obj"].read_bytes(), "_score_rate",
                                    "_score_pool")
    out.append(failure(
        "N5_incorrect_relocation_target",
        "score slice whose first data relocation names a different (valid) "
        "symbol than the original instruction at that offset",
        dict(obj=mutated, prog=p, db=db), score["evaluation"],
        x.RELOCATION_TARGET_MISMATCH,
        evidence=dict(declared_symbol="_score_pool",
                      original_symbol="_score_rate",
                      original_target=db["_score_rate"]["addr"],
                      declared_target=db["_score_pool"]["addr"])))
    case = fixtures.jump_table()
    out.append(failure(
        "N6_shared_jump_table",
        "indirect jump through a table that the slice does not own (outside [lo, hi))",
        case, evaluate_region(case["prog"], case["mod"], case["db"], case["candidate"]),
        x.INCOMPLETE_CLOSURE,
        evidence=dict(table_object_offset=0x10,
                      slice=[0, 0x10],
                      finding_codes=["outgoing_text_pointer", "unproven_indirect_jump"])))
    return out


def production_diff():
    r = subprocess.run(["git", "diff", "--name-only", BASELINE, "--", *PRODUCTION_PATHS],
                       capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode:
        raise RuntimeError(r.stderr)
    return [line for line in r.stdout.splitlines() if line.strip()]


def collect():
    p, funcs, datas, db = inputs()
    index = OriginalIndex(p)
    compiler = Path(oldcc.require()) / "binnt/wcc386.exe"
    old_out = b.OUT
    b.OUT = E4_OUT
    try:
        return _collect(p, funcs, datas, db, index, compiler, old_out)
    finally:
        b.OUT = old_out


def _collect(p, funcs, datas, db, index, compiler, old_out):
    print("E4: compile and verify the Build A baseline", flush=True)
    objects = baseline(p, funcs, db)
    print("E4: extract ScoreTickIncome", flush=True)
    score = positive_thread(
        SCORE, p, db, index, objects, funcs, datas, "score",
        "ScoreTickIncome 0x24e90 extracted from the multi-function score_reference "
        "fixture (mismatching RankName/ScoreSetPage, 3-byte alignment tail)")
    print("E4: extract FarmPanelChanged", flush=True)
    farm = positive_thread(
        FARM, p, db, index, objects, funcs, datas, "farm",
        "FarmPanelChanged 0x28254 extracted from panel_state_reference.c "
        "(mismatching UnitPanelStateChanged, call across the sibling, 5 data refs)")
    print("E4: controlled oracle cases", flush=True)
    controlled = controlled_case()
    direct = direct_case()
    print("E4: multi-chunk LEDATA case", flush=True)
    chunked = chunk_case()
    print("E4: negative controls", flush=True)
    negative = negatives(p, db, index)
    changed = production_diff()
    if changed:
        raise AssertionError(f"production files changed: {changed}")
    return dict(
        experiment="E4",
        baseline=BASELINE,
        contract="docs/research/build-codegen/contracts/E4-contract.md",
        inputs=dict(compiler="Watcom 10.0a", compiler_sha256=digest(compiler.read_bytes()),
                    original_exe_sha256=digest((ROOT / "original/install/war.exe").read_bytes()),
                    symbol_db_entries=len(db)),
        build_a=dict(le_fixups=LE_FIXUPS, baseline_c_objects=len(objects),
                     baseline_c_functions=sum(len(o["funcs"]) for o in objects)),
        positives=[score, farm],
        controlled=[controlled, direct],
        chunking=chunked,
        negatives=negative,
        conclusions=dict(
            build_a="extractable: both real slices link to a byte-identical "
                    "Build A image with 0/8770 differing LE fixups",
            intra_tu_call="supported for named rel32 targets (EXTDEF + "
                          "self-relative FIXUPP32), both compiled-fixup and "
                          "plain-displacement forms",
            data_anchors="CONST literals integrate through E5 Fix B3 "
                         "wc1_anchor_* with an identical oracle executable",
            chunking="supported: LEDATA32 is re-split before any straddling "
                     "4-byte field; wlink links the result identically",
            fail_closed="all six RFC section 6.2 negative classes rejected with "
                        "their exact reason code",
            production_changes=0),
    )


def run():
    results = collect()
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(f"E4: {RESULTS.relative_to(ROOT)}", flush=True)
    return results


if __name__ == "__main__":
    run()
