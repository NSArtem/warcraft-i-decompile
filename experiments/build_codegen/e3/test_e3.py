"""Real Watcom objects and independent synthetic OMF/LE controls for E3."""
import struct

import pytest
from wc1 import le, omf

from experiments.build_codegen.e0.controls import synthetic as image
from experiments.build_codegen.e3.fixtures import synthetic
from experiments.build_codegen.e3.partial_matcher import (
    CandidateRegion, Conditional, Mismatch, Unsupported, VerifiedRegion, evaluate_region,
)
from experiments.build_codegen.e3.run_e3 import ROOT, SCORE, SCORE_FIXTURE, real_cases, synthetic_cases


@pytest.fixture(scope="module")
def real():
    return real_cases()


@pytest.fixture(scope="module")
def controls():
    return synthetic_cases()


def codes(region):
    return {f["code"] for f in region["findings"]}


def test_dialog_shared_ret_and_folded_alias_block_extraction(real):
    case = real["dialog"]
    regions = case["regions"]
    for name in ("DialogItemHitTest_", "DialogHighlightOn_", "DialogHighlightOff_"):
        result = regions[name]
        assert result["function_verdicts"][name] == "MISMATCH"
        assert result["region_verdict"] != "REGION_MATCH"
    off = regions["DialogHighlightOff_"]
    assert off["region_verdict"] == "MISMATCH"
    assert off["dependency_classification"] == "blocked_by_sibling_dependency"
    assert off["candidate"]["obj_lo"] == regions["DialogHighlightOn_"]["candidate"]["obj_lo"]
    assert {"relative_target_mismatch", "public_layout_mismatch", "outgoing_rel8_dependency"} <= codes(off)
    short, = [ref for ref in off["outgoing_refs"] if ref["encoding"] == "rel8"]
    assert short["original_target"] == 0x16D31
    assert short["object_target"] == 0x5E


def test_farm_uses_existing_symbolic_sibling_fixup(real):
    case = real["farm"]
    assert case["object_wide"]["verdict"] == "MISMATCH"
    farm = case["regions"]["FarmPanelChanged_"]
    assert farm["function_verdicts"] == {"FarmPanelChanged_": "MATCH"}
    assert farm["region_verdict"] == "REGION_MATCH"
    assert farm["dependency_classification"] == "proven_standalone_region"
    assert farm["findings"] == []
    edge, = farm["outgoing_refs"]
    assert edge["encoding"] == "sibling_extdef_fixupp"
    assert edge["original_target"] == 0x281F4
    assert edge["symbol"] == "UnitPanelStateChanged_"
    assert case["regions"]["UnitPanelStateChanged_"]["region_verdict"] == "MISMATCH"


def test_score_swapped_matches_with_mismatching_siblings(real):
    baseline = real["score_baseline"]["regions"]["ScoreTickIncome_"]
    assert baseline["region_verdict"] == "MISMATCH"
    finding, = baseline["findings"]
    assert finding["code"] == "byte_mismatch"
    assert (finding["orig_addr"], finding["evidence"]["got"], finding["evidence"]["want"]) == (
        0x24EB9, 0x02, 0x10)
    assert (ROOT / SCORE_FIXTURE).read_text() == (ROOT / SCORE).read_text().replace(
        "sum = score + delta;", "sum = delta + score;")
    case = real["score_swapped"]
    regions = case["regions"]
    assert case["object_wide"]["verdict"] == "MISMATCH"
    assert regions["RankName_"]["region_verdict"] == "MISMATCH"
    assert regions["ScoreSetPage_"]["region_verdict"] == "MISMATCH"
    tick = regions["ScoreTickIncome_"]
    assert tick["function_verdicts"] == {"ScoreTickIncome_": "MATCH"}
    assert tick["region_verdict"] == "REGION_MATCH"
    assert tick["proof"]["orig_end"] == 0x24EDD
    assert tick["proof"]["trailing_filler_size"] == 3
    assert tick["outgoing_refs"] == []


def test_shifted_const_requires_region_local_symbol_identity(controls):
    case = controls["shifted_const"]
    assert case["object_wide"]["verdict"] == "MISMATCH"
    assert case["object_wide"]["segment_bases"][2] == 0x50000
    assert case["object_wide"]["anchor_conflicts"]
    assert case["regions"]["Sibling_"]["function_verdicts"]["Sibling_"] != "MATCH"
    probe = case["regions"]["Probe_"]
    assert probe["region_verdict"] == "REGION_MATCH"
    assert 2 not in probe["segment_bases"]
    data = probe["proof"]["data_deps"]
    assert [(d["obj_start"], d["orig_start"], d["size"], d["data_scope"]) for d in data] == [
        (7, 0x50002, 4, "per_symbol_const"), (11, 0x50006, 4, "per_symbol_const")]


@pytest.mark.parametrize(("case", "reason"), [
    ("mutable_shift", "unproven_data_boundary"),
    ("corrupted_const", "symbol_data_mismatch"),
    ("aliased_const", "data_identity_mismatch"),
    ("aliased_original", "data_identity_mismatch"),
    ("wrong_sibling", "unproven_sibling_target"),
    ("unresolved_sibling", "unproven_sibling_target"),
])
def test_negative_controls_fail_closed(controls, case, reason):
    probe = controls[case]["regions"]["Probe_"]
    assert probe["region_verdict"] in ("MISMATCH", "UNSUPPORTED")
    assert probe["function_verdicts"]["Probe_"] in ("MISMATCH", "UNSUPPORTED")
    assert probe["proof"] is None
    assert reason in codes(probe)


def test_independent_mutable_boundaries_authorize_exact_symbol_map(controls):
    probe = controls["proven_mutable_shift"]["regions"]["Probe_"]
    assert probe["region_verdict"] == "REGION_MATCH"
    assert {d["data_scope"] for d in probe["proof"]["data_deps"]} == {"per_symbol_mutable"}


def test_outgoing_rel8_is_conditional_and_incoming_is_diagnostic(controls):
    case = controls["outgoing_rel8"]
    probe = case["regions"]["Probe_"]
    assert probe["region_verdict"] == "CONDITIONAL"
    assert probe["proof"] is None
    assert codes(probe) == {"outgoing_rel8_dependency"}
    sibling = case["regions"]["Sibling_"]
    assert {ref["origin"] for ref in sibling["incoming_refs"]} == {"original", "object"}
    p, m, db = image(b"\x40\xeb\x00\xc3",
                     original=b"\x48\xeb\x00\xc3",
                     publics={"Bad_": (1, 0), "Probe_": (1, 3)})
    value = evaluate_region(p, m, db, CandidateRegion(3, 4, 0x10003))
    assert isinstance(value.proof, VerifiedRegion)
    assert {ref["origin"] for ref in value.incoming_refs} == {"original", "object"}


def test_direct_rel32_requires_rewrite_even_when_sibling_mismatches(controls):
    case = controls["direct_rel32"]
    probe = case["regions"]["Probe_"]
    assert probe["function_verdicts"] == {"Probe_": "MATCH"}
    assert probe["region_verdict"] == "REGION_MATCH_WITH_REL32_REWRITE_NEEDED"
    assert probe["dependency_classification"] == "requires_rel32_extraction"
    edge, = probe["proof"]["outgoing_refs"]
    assert (edge["encoding"], edge["original_target"], edge["object_target"]) == ("rel32", 0x10008, 6)
    assert case["regions"]["Sibling_"]["region_verdict"] == "MISMATCH"


def test_group_closes_rel8_only_when_target_is_also_verified():
    p, m, db = synthetic.branch("outgoing_rel8")
    group = CandidateRegion(0, 4, 0x10000)
    assert isinstance(evaluate_region(p, m, db, group).proof, Mismatch)
    m.segments[0].data[2] = 0x48
    result = evaluate_region(p, m, db, group)
    assert isinstance(result.proof, VerifiedRegion)
    assert result.outgoing_refs == []
    assert result.functions == {"Probe_": "MATCH", "Sibling_": "MATCH"}


def test_closed_leading_bytes_must_be_checked_even_when_body_matches():
    p, m, db = image(b"\x90\xc3", publics={"Probe_": (1, 1)})
    whole = CandidateRegion(0, 2, 0x10000)
    assert isinstance(evaluate_region(p, m, db, whole).proof, VerifiedRegion)
    skipped = evaluate_region(p, m, db, CandidateRegion(1, 2, 0x10001))
    assert isinstance(skipped.proof, Mismatch)
    assert any(f["code"] == "unverified_leading_bytes" for f in skipped.result.findings)
    m.segments[0].data[0] = 0x40
    assert isinstance(evaluate_region(p, m, db, whole).proof, Mismatch)


@pytest.mark.parametrize(("compiled", "original", "finding"), [
    (b"\x90", b"\x90\xc3", "truncated_function"),
    (b"\xc3\x40\xc3", b"\xc3", "extent_retry_rejected"),
])
def test_no_truncated_or_unverified_tail(compiled, original, finding):
    p, m, db = image(compiled, original=original)
    value = evaluate_region(p, m, db, CandidateRegion(0, len(compiled), 0x10000))
    assert not isinstance(value.proof, VerifiedRegion)
    assert any(f["code"] == finding for f in value.result.findings)


def test_out_of_bounds_fixup_in_sibling_is_fatal():
    p, m, db = image(b"\xc3\xc3", publics={"Probe_": (1, 0), "Sibling_": (1, 1)})
    m.segments[0].fixups.append(omf.Fixup(4, 9, False, "seg", 1, 0))
    val = evaluate_region(p, m, db, CandidateRegion(0, 1, 0x10000))
    assert isinstance(val.proof, Unsupported)
    assert any(f["code"] == "fixup_out_of_bounds" for f in val.result.findings)


def test_referenced_metadata_is_rejected_even_if_symbol_db_matches():
    p, m, db, bounds = synthetic.string_pool()
    m.segments.append(omf.Segment("$$SYMBOLS", "DEBSYM", 1, 8, bytearray(8)))
    m.statics["Fake"] = (3, 0)
    db["Fake"] = dict(addr=0x50002, link_name="Fake")
    f = m.segments[0].fixups[1]
    f.target_kind, f.target = "ext", "Fake"
    val = evaluate_region(p, m, db, CandidateRegion(7, 18, 0x10007), boundaries=bounds)
    assert isinstance(val.proof, Unsupported)
    assert any(f["code"] == "runtime_reference_to_debug" for f in val.result.findings)


def test_whole_segment_checks_pointer_fixups_in_both_directions():
    base, target = 0x50000, 0x50004
    p, m, db = image(b"\xb8\0\0\0\0\xc3",
                     [omf.Fixup(1, 9, False, "seg", 2, 0)],
                     original=b"\xb8" + struct.pack("<I", base) + b"\xc3",
                     original_fixes=[(1, base)])
    ds = le.Obj(2, 5, base, le.OBJ_READ | le.OBJ_WRITE, 1, 1)
    p.image[2] = struct.pack("<I", target) + b"\x7f"
    p.le.obj_at = lambda a: p.code if p.code.base <= a < p.code.end else (
        ds if ds.base <= a < ds.end else None)
    p.fix_at[base] = (le.Fixup(2, 0, 7, 2, 4), target)
    pointer = omf.Fixup(0, 9, False, "seg", 2, 0)
    data = omf.Segment("CONST", "DATA", 1, 5, bytearray(b"\x04\0\0\0\x7f"), [pointer])
    m.segments.append(data)
    candidate = CandidateRegion(0, 6, 0x10000)
    matched = evaluate_region(p, m, db, candidate)
    assert isinstance(matched.proof, VerifiedRegion)
    dep, = matched.proof.data_deps
    assert dict(dep)["data_scope"] == "whole_segment"
    assert matched.result.metrics["data_fixups_checked"] == 1
    data.fixups.clear()
    data.data[:4] = struct.pack("<I", target)
    rejected = evaluate_region(p, m, db, candidate)
    assert isinstance(rejected.proof, Mismatch)
    assert any(f["code"] == "missing_compiled_absolute_fixup" for f in rejected.result.findings)


def test_interior_direct_rel32_is_never_promoted_to_sibling_entry():
    p, m, db = synthetic.branch("direct_rel32")
    m.segments[0].data[1] = 2  # offset 7 is inside Sibling, whose entry is 6
    value = evaluate_region(p, m, db, CandidateRegion(0, 6, 0x10000))
    assert isinstance(value.proof, Mismatch)
    assert any(f["code"] == "blocked_by_sibling_dependency" for f in value.result.findings)


def test_sibling_with_unsupported_fixup_does_not_supply_data_anchors():
    p, m, db, bounds = synthetic.string_pool()
    f = m.segments[0].fixups[0]
    f.target_kind, f.target = "grp", "DGROUP"
    val = evaluate_region(p, m, db, CandidateRegion(7, 18, 0x10007), boundaries=bounds)
    assert isinstance(val.proof, VerifiedRegion)


def test_per_symbol_const_rejects_an_interior_offset_even_with_matching_bytes():
    p, m, db, bounds = synthetic.string_pool()
    m.segments[0].data[8] = 8  # the address of "ne" inside the "one" literal
    p.fix_at[0x10008] = (le.Fixup(1, 8, 7, 2, 3), 0x50003)
    p.image[1][8:12] = struct.pack("<I", 0x50003)
    val = evaluate_region(p, m, db, CandidateRegion(7, 18, 0x10007), boundaries=bounds)
    assert isinstance(val.proof, Unsupported)
    assert any(f["code"] == "unproven_data_boundary" for f in val.result.findings)


def test_no_inferred_fallthrough_outside_slice():
    p, m, db = image(b"\x40\xc3", publics={"Probe_": (1, 0), "Sibling_": (1, 1)})
    val = evaluate_region(p, m, db, CandidateRegion(0, 1, 0x10000))
    assert val.functions == {"Probe_": "MATCH"}
    assert isinstance(val.proof, Conditional)
    assert any(f["code"] == "unproven_end_of_control_flow" for f in val.result.findings)
