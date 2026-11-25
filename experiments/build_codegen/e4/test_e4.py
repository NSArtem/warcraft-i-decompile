"""E4 checks: selective OMF32 extraction against Build A and fail-closed controls.

The Build A baseline is compiled once per session.  The real cases are then
re-extracted and re-linked here, so the suite proves the extractor and not just
the committed artifact: every positive case is compared with the deterministic
`results.json` record *and* independently checked for its E3 proof, its
byte-invariant slice, its relocation transforms and its link/oracle verdict.

Generated artifacts stay under `build/e4/` (see `fixtures.support`); the
committed machine evidence is `docs/research/build-codegen/results/e4/`.
"""
from pathlib import Path
from types import SimpleNamespace
import json
import os
import re
import struct

import pytest

from wc1 import omf
from experiments.build_codegen.e0.matcher_proto import OriginalIndex
from experiments.build_codegen.e3.partial_matcher import (
    CandidateRegion, VerifiedRegion, evaluate_region,
)
from experiments.build_codegen.e5 import build_e5 as b
from . import fixtures, omf_extract as x, run_e4
from .fixtures import builder, support

SCORE_LO, SCORE_HI, SCORE_ORIG = 0, 77, 0x24E90
FARM_LO, FARM_HI, FARM_ORIG = 0x80, 0xC4, 0x28254
CODE_BASE = fixtures.CODE_BASE


# --------------------------------------------------------------------- fixtures
@pytest.fixture(scope="module")
def results():
    """One fresh E4 collection; the checkout root must not gain any file."""
    before = {p.name for p in run_e4.ROOT.iterdir()}
    collected = run_e4.collect()
    assert {p.name for p in run_e4.ROOT.iterdir()} == before
    return collected


@pytest.fixture(scope="module")
def context(results):
    p, funcs, datas, db = run_e4.inputs()
    return SimpleNamespace(p=p, funcs=funcs, datas=datas, db=db,
                           index=OriginalIndex(p))


def by_id(records, name):
    return next(record for record in records if record["id"] == name)


def assert_byte_invariant(p, mod, lo, hi, base):
    """Every byte outside a relocated off32 field equals the original image."""
    text = bytes(mod.seg("_TEXT")[1].data)
    obj = p.le.obj_at(base)
    assert obj is not None and base + hi - lo <= obj.end
    want = bytes(p.image[obj.index][base - obj.base:base - obj.base + hi - lo])
    masked = set()
    for fu in mod.segments[mod.seg("_TEXT")[0] - 1].fixups:
        if fu.loc == x.LOC32 and lo <= fu.offset and fu.offset + 4 <= hi:
            masked.update(range(fu.offset, fu.offset + 4))
    diffs = [(lo + i, text[lo + i], want[i]) for i in range(hi - lo)
             if lo + i not in masked and text[lo + i] != want[i]]
    assert diffs == []
    return len(masked)


def walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from walk_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_strings(item)


# ------------------------------------------------------------- artifact health
def test_committed_results_match_a_fresh_run(results):
    """A separate process produced the committed file: it must be identical."""
    expected = json.dumps(results, indent=2, sort_keys=True) + "\n"
    assert run_e4.RESULTS.read_text() == expected


def test_results_are_path_free_and_untimed(results):
    """No checkout, temp, compiler-mirror path or timestamp may leak."""
    strings = list(walk_strings(results))
    assert strings
    for value in strings:
        assert not value.startswith(("/", "\\", "~")), value
        assert not re.match(r"^[A-Za-z]:[\\/]", value), value
        assert not re.search(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", value), value
    text = run_e4.RESULTS.read_text()
    for marker in ("/mnt/", "/tmp/", "/nix/", "wc1e5-", str(run_e4.ROOT)):
        assert marker not in text


def test_results_schema_and_trust_boundary(results):
    assert results["experiment"] == "E4"
    assert results["baseline"] == run_e4.BASELINE
    assert results["contract"] == "docs/research/build-codegen/contracts/E4-contract.md"
    assert results["inputs"]["compiler"] == "Watcom 10.0a"
    assert results["inputs"]["symbol_db_entries"] == 2324
    assert results["inputs"]["compiler_sha256"] == \
        "8fee7d6ab3f2c06a0a874135e3898386898679e7dd53993fcc508e296364767d"
    assert results["inputs"]["original_exe_sha256"] == \
        "1e966220bf09ab007c49c5ea5ebc42eb494f5cf2f74f894d3969b6115df8d8a9"
    assert results["build_a"] == dict(baseline_c_objects=514, baseline_c_functions=519,
                                      le_fixups=8770)
    assert results["conclusions"]["production_changes"] == 0
    assert set(results["conclusions"]) == {
        "build_a", "intra_tu_call", "data_anchors", "chunking", "fail_closed",
        "production_changes"}
    assert run_e4.E4_OUT == run_e4.ROOT / "build/e4/ba"
    assert support.OUT == run_e4.ROOT / "build/e4"
    assert str(run_e4.RESULTS).startswith(
        str(run_e4.ROOT / "docs/research/build-codegen/results/e4"))


def test_compiler_facing_paths_stay_short(results):
    """10.0a's fixed command-line buffers: every E4 compile path is bounded."""
    paths = [support.HERE / "controlled_tu.c",
             support.ROOT / run_e4.SCORE[0],
             support.ROOT / run_e4.FARM[0],
             support.ROOT / run_e4.DIALOG[0],
             support.OBJ / "scoretickincome.obj",
             support.OBJ / "controlled_tu.obj",
             run_e4.E4_OUT / "b000.obj"]
    assert b.COMPILER_PATH_LIMIT <= 112
    for path in paths:
        short = b.compiler_path(path)
        assert len(str(short)) <= b.COMPILER_PATH_LIMIT, (path, short)
        assert os.path.realpath(short) == os.path.realpath(path)


# ------------------------------------------------------------- positive case 1
def test_positive_1_score_tick_income(context, results):
    """ScoreTickIncome 0x24e90 from the multi-function score_reference TU."""
    got = run_e4.extract_real(context.p, context.db, context.index, run_e4.SCORE)
    proof = got["evaluation"].proof
    assert isinstance(proof, VerifiedRegion)
    assert proof.candidate == CandidateRegion(SCORE_LO, SCORE_HI, SCORE_ORIG)
    assert proof.orig_end == SCORE_ORIG + SCORE_HI
    assert proof.verification_scope == "extracted_slice"
    assert [name for _, name in proof.entries] == ["ScoreTickIncome_"]

    prov = got["provenance"]
    assert prov["invariants"] == dict(region_match=True, byte_invariant=True,
                                      non_relocated_bytes=53, relocated_fields=6)
    text = bytes(got["mod"].seg("_TEXT")[1].data)
    assert len(text) == 192                  # RankName/ScoreSetPage stay behind
    assert prov["compiled_slice_sha256"] == x.text_sha256(text[SCORE_LO:SCORE_HI])
    assert prov["compiled_slice_sha256"] == \
        "6e6b8bc683a4cabde6feba4751e6ff7cbf824af6ae7d3dafe26a0ebdd862ef8f"
    assert prov["source_object_loadable_sha256"] == \
        "9bcbedb24fcf762ff6251be860a3e8d6870599295d922d18fa0562e168eeebe6"
    assert prov["extracted_object_loadable_sha256"] == \
        "057b4f56b9dc88caa53d42d1052abed7301c5e84c428a4a7e6fc7477b4774861"
    assert prov["evidence_digest"] == \
        "fc0cb3be0218989df06569a155a774f4327debe661a0769c1951f5d38b3e88aa"
    assert prov["extracted_object_bytes"] == 787
    assert assert_byte_invariant(context.p, got["mod"], SCORE_LO, SCORE_HI,
                                 SCORE_ORIG) == 24

    transforms = prov["transforms"]
    assert [t["symbol"] for t in transforms] == [
        "_score_rate", "_game_mode_dword_low", "_player_score", "_score_cap",
        "_player_score", "_score_pool"]
    assert {t["kind"] for t in transforms} == {"external"}
    assert all(t["self_rel"] is False and t["inline_before"] == 0 for t in transforms)
    assert {d["symbol"] for d in prov["dropped"]
            if d["reason"] == "public_outside_slice"} == {"RankName_", "ScoreSetPage_"}
    assert prov["added_extdefs"] == []
    assert prov["instructions"] == 25 and len(prov["branches"]) == 2

    objects = run_e4.baseline(context.p, context.funcs, context.db)
    fresh = run_e4.positive_thread(
        run_e4.SCORE, context.p, context.db, context.index, objects,
        context.funcs, context.datas, "score",
        "ScoreTickIncome 0x24e90 extracted from the multi-function score_reference "
        "fixture (mismatching RankName/ScoreSetPage, 3-byte alignment tail)")
    assert fresh == results["positives"][0]
    assert fresh["build_a"]["identical"] is True
    assert fresh["build_a"]["byte_diffs"] == 0
    assert fresh["build_a"]["original_fixups"] == 8770
    assert fresh["build_a"]["linked_fixups"] == 8770
    assert fresh["build_a"]["only_original"] == fresh["build_a"]["only_linked"] == 0
    assert fresh["build_a"]["c_functions"] == results["build_a"]["baseline_c_functions"] + 1
    assert fresh["build_a"]["c_objects"] == results["build_a"]["baseline_c_objects"] + 1


# ------------------------------------------------------------- positive case 2
def test_positive_2_farm_panel_changed(context, results):
    """FarmPanelChanged 0x28254 over the mismatching UnitPanelStateChanged."""
    got = run_e4.extract_real(context.p, context.db, context.index, run_e4.FARM)
    proof = got["evaluation"].proof
    assert isinstance(proof, VerifiedRegion)
    assert proof.candidate == CandidateRegion(FARM_LO, FARM_HI, FARM_ORIG)
    assert proof.orig_end == FARM_ORIG + (FARM_HI - FARM_LO)
    assert proof.verification_scope == "extracted_slice"
    assert [name for _, name in proof.entries] == ["FarmPanelChanged_"]

    prov = got["provenance"]
    assert prov["invariants"] == dict(region_match=True, byte_invariant=True,
                                      non_relocated_bytes=44, relocated_fields=6)
    text = bytes(got["mod"].seg("_TEXT")[1].data)
    assert len(text) == 196
    assert prov["compiled_slice_sha256"] == x.text_sha256(text[FARM_LO:FARM_HI])
    assert prov["compiled_slice_sha256"] == \
        "d39187a5b15dac2e1a559c78fde4f4a8bbc906309c6ee3b89f8ab73be08de00a"
    assert prov["source_object_loadable_sha256"] == \
        "2992d2a839750fe99064c8cad45b9f15df55736190d207e4a404c79af78a1075"
    assert prov["extracted_object_loadable_sha256"] == \
        "5c4d7f4d991d03688039a339ecfdf366ba0e3bcfbe277e7299b5b7bcb883bf0b"
    assert prov["evidence_digest"] == \
        "23e0d0d65dd741eff3c9933f4e02e3aeba6152646e8e272b6989246b65d44703"
    assert prov["extracted_object_bytes"] == 794
    assert assert_byte_invariant(context.p, got["mod"], FARM_LO, FARM_HI,
                                 FARM_ORIG) == 24

    transforms = prov["transforms"]
    data = [t for t in transforms if t["kind"] == "external"]
    assert [t["symbol"] for t in data] == [
        "_player_active_men", "_player_summoned", "_status_men_used",
        "_status_men_grown", "_player_food"]
    call = next(t for t in transforms if t["kind"] == "intra_tu_extdef")
    assert call["symbol"] == "UnitPanelStateChanged_"
    assert call["target_address"] == 0x281F4
    assert call["self_rel"] is True and call["inline_before"] == 0
    assert call["transform"] == "kept EXTDEF + self-relative FIXUPP32"
    assert any(d["reason"] == "public_outside_slice" and
               d["symbol"] == "UnitPanelStateChanged_" for d in prov["dropped"])
    assert prov["added_extdefs"] == []
    assert prov["instructions"] == 22 and len(prov["branches"]) == 3

    objects = run_e4.baseline(context.p, context.funcs, context.db)
    fresh = run_e4.positive_thread(
        run_e4.FARM, context.p, context.db, context.index, objects,
        context.funcs, context.datas, "farm",
        "FarmPanelChanged 0x28254 extracted from panel_state_reference.c "
        "(mismatching UnitPanelStateChanged, call across the sibling, 5 data refs)")
    assert fresh == results["positives"][1]
    assert fresh["build_a"]["identical"] is True
    assert fresh["build_a"]["byte_diffs"] == 0
    assert fresh["build_a"]["original_fixups"] == 8770
    assert fresh["build_a"]["linked_fixups"] == 8770
    assert fresh["build_a"]["only_original"] == fresh["build_a"]["only_linked"] == 0


# ------------------------------------------------------------- positive case 3
def test_positive_3_intra_tu_call_and_const_anchor(results):
    """10.0a [A, B_mismatch, C]: extract A; call C; anchor the CONST literal."""
    got = run_e4.controlled_case()
    ref = by_id(results["controlled"], "positive_3_const_and_intra_tu_call")
    assert got == ref
    assert got["oracle"]["identical"] is True
    assert "IDENTICAL" in got["oracle"]["comparison"]
    assert got["layout"]["extracted"] == [0, 18]
    assert got["layout"]["functions"] == [["E4_A_", 0, 18], ["E4_B_", 32, 36],
                                         ["E4_C_", 48, 62]]
    assert got["layout"]["text_length"] == 62
    assert got["extraction"]["chunks"] == [dict(object_offset=0, size=18)]
    assert got["extraction"]["invariants"] == dict(region_match=True, byte_invariant=True,
                                                   non_relocated_bytes=10, relocated_fields=2)
    assert got["anchor"] == dict(symbol="wc1_anchor_20000", address=0x20000, literal_size=17)
    assert got["data_plan"]["scopes"] == ["whole_segment"]
    assert got["slice_externs"] == ["E4_C_", "wc1_anchor_20000"]
    assert got["slice_fixups"] == [[2, True, "ext", "E4_C_"],
                                   [10, False, "ext", "wc1_anchor_20000"]]
    call = got["transforms"][0]
    assert call["kind"] == "intra_tu_extdef" and call["symbol"] == "E4_C_"
    assert call["target_address"] == 0x10030          # C at object offset 48
    assert call["self_rel"] is True
    anchor = got["transforms"][1]
    assert anchor["kind"] == "data_segment" and anchor["segment"] == 2
    assert anchor["self_rel"] is False
    assert got["extraction"]["extracted_object_loadable_sha256"] == \
        "285375251640dd583b4eaa9ffa12ac88fee4cd48ae7a140a3395e8a44ab4430c"


def test_positive_3b_direct_unfixed_rel32_and_omf16_normalization(results):
    """NASM's plain (unfixed) `call rel32` is recovered from the symbol table."""
    got = run_e4.direct_case()
    ref = by_id(results["controlled"], "positive_3b_direct_unfixed_rel32")
    assert got == ref
    assert got["oracle"]["identical"] is True
    assert got["slice_text"] == "5589e5e8000000005dc3"
    assert got["call"] == dict(offset=4, symbol="E4_C", target_object_offset=32,
                               target_address=0x10020, inline_before=24,
                               inline_after=0)
    assert got["added_extdefs"] == ["E4_C"]
    assert got["slice_fixups"] == [[4, True, "ext", "E4_C"]]
    assert got["transforms"][0]["kind"] == "direct_rel32_to_extdef"
    assert got["transforms"][0]["transform"] == "EXTDEF + self-relative FIXUPP32"
    assert got["extraction"]["invariants"] == dict(region_match=True, byte_invariant=True,
                                                   non_relocated_bytes=6, relocated_fields=1)
    assert got["extraction"]["extracted_object_loadable_sha256"] == \
        "572e0357a3e333349894da1e8183e51df85186a1900a8cdbeadb86711f4e88c7"

    # The source is OMF16; the extracted object is OMF32 (representation only).
    case = fixtures.direct_call()
    source_types = {t for t, _ in x.read_records(Path(case["obj"]).read_bytes())}
    assert {0x90, 0x98, 0xA0} <= source_types
    packed, prov = x.extract(case["obj"],
                             evaluate_region(case["prog"], case["mod"], case["db"],
                                             case["candidate"], index=case["index"]),
                             case["db"], case["prog"], index=case["index"])
    extracted_types = {t for t, _ in x.read_records(packed)}
    assert extracted_types.isdisjoint({0x90, 0x98, 0x9C, 0xA0})
    assert {0x91, 0x99, 0x9D, 0xA1} <= extracted_types
    assert prov["record_normalization"] == "OMF16 records normalized to OMF32 widths"


# ------------------------------------------------------------- positive case 4
def test_positive_4_multi_chunk_ledata(results):
    """>1024 B body: split LEDATA32 before the 4-byte field at 1022-1026."""
    got = run_e4.chunk_case()
    assert got == results["chunking"]
    assert got["oracle"]["identical"] is True
    assert got["text_length"] == 1500 and got["field_offset"] == 1022
    assert got["chunks"] == [dict(object_offset=0, size=1022),
                             dict(object_offset=1022, size=478)]
    assert got["chunk_count"] == 2
    assert got["field_chunk"] == dict(object_offset=1022, size=478)
    assert got["invariants"] == dict(region_match=True, byte_invariant=True,
                                     non_relocated_bytes=1496, relocated_fields=1)
    assert got["extracted_object_loadable_sha256"] == \
        "04209a7956cc741b4588a6fbd955b99399573755d3b33f32e64069b1e52433ad"

    # Re-extract and inspect the emitted LEDATA32 records directly.
    case = fixtures.long_chunk()
    packed, prov = x.extract(
        case["obj"],
        evaluate_region(case["prog"], case["mod"], case["db"], case["candidate"]),
        case["db"], case["prog"])
    field = case["field"]
    slices = []
    for record_type, body in x.read_records(packed):
        if record_type == 0xA1:
            _, q = omf._idx(body, 0)
            off = int.from_bytes(body[q:q + 4], "little")
            slices.append((off, len(body) - q - 4))
    assert slices == [(0, 1022), (1022, 478)]
    assert all(size <= x.CHUNK == 1024 for _, size in slices)
    assert all(not (field < off < field + 4) for off, _ in slices[:-1])
    assert prov["chunks"] == got["chunks"]


# ----------------------------------------------------------- fail-closed rules
def test_all_negative_controls_reject_fail_closed(context, results):
    fresh = run_e4.negatives(context.p, context.db, context.index)
    assert fresh == results["negatives"]
    assert [n["id"] for n in fresh] == [
        "N1_on", "N1_off", "N2_interior_target", "N3_unknown_symbol_from_war_exe",
        "N4_unproven_mutable_layout", "N4_misanchored_mutable_layout",
        "N5_incorrect_relocation_target", "N6_shared_jump_table"]
    for record in fresh:
        assert record["fail_closed"] is True
        assert record["reason"] == record["expected_reason"]
        assert record["message"]
    # All six RFC section 6.2 classes are covered by the control set.
    assert {n["reason"] for n in fresh} == {
        x.OUTGOING_REL8, x.INTERIOR_TARGET, x.AMBIGUOUS_SYMBOL,
        x.DATA_LAYOUT_MISMATCH, x.RELOCATION_TARGET_MISMATCH, x.INCOMPLETE_CLOSURE}


def test_n1_outgoing_rel8_both_folded_dialog_highlights(results):
    """N1b: the real DialogHighlightOff 0x16d48 is not standalone-extractable."""
    on = by_id(results["negatives"], "N1_on")
    off = by_id(results["negatives"], "N1_off")
    assert off["reason"] == x.OUTGOING_REL8
    assert off["evidence"]["candidate"] == dict(obj_lo=95, obj_hi=112,
                                                orig_start=0x16D48)
    assert on["reason"] == x.OUTGOING_REL8
    for record in (on, off):
        assert record["evidence"]["region_verdict"] == "MISMATCH"
        assert record["evidence"]["rel8"] == [[104, 94, 0x16D31]]
        assert "outgoing_rel8_dependency" in record["evidence"]["finding_codes"]
        assert "byte_mismatch" in record["evidence"]["finding_codes"]


def test_n2_to_n6_rejection_evidence(results):
    n2 = by_id(results["negatives"], "N2_interior_target")
    assert n2["evidence"]["call_site"] == 0
    assert n2["evidence"]["original_target"] == CODE_BASE + 0x10 + 1

    n3 = by_id(results["negatives"], "N3_unknown_symbol_from_war_exe")
    assert n3["evidence"]["sibling"] == "UnitPanelStateChanged_"
    assert n3["evidence"]["simplest_guess"] == 0x281F4
    assert n3["evidence"]["database_entry_removed"] is True

    n4 = by_id(results["negatives"], "N4_unproven_mutable_layout")
    assert n4["message"].startswith("nonempty local data segment")
    misanchored = by_id(results["negatives"], "N4_misanchored_mutable_layout")
    assert misanchored["reason"] == x.DATA_LAYOUT_MISMATCH
    assert "E0 data check" in misanchored["message"]

    n5 = by_id(results["negatives"], "N5_incorrect_relocation_target")
    assert n5["evidence"] == dict(declared_symbol="_score_pool",
                                  declared_target=0x5A0CE,
                                  original_symbol="_score_rate",
                                  original_target=0x5A0CC)

    n6 = by_id(results["negatives"], "N6_shared_jump_table")
    assert n6["evidence"]["slice"] == [0, 0x10]
    assert n6["evidence"]["table_object_offset"] == 0x10
    assert n6["evidence"]["finding_codes"] == ["outgoing_text_pointer",
                                               "unproven_indirect_jump"]


# ------------------------------------------------------- extractor unit checks
def test_byte_invariant_self_check_rejects_a_changed_immediate():
    """A stale proof cannot smuggle a changed non-relocated byte into a slice."""
    code = bytes.fromhex("b811223344c3")            # mov eax,0x44332211; ret
    prog, db = fixtures.synthetic_program(code, {"E4_Mut": (1, 0)})

    def module(data):
        return builder.build(
            segments=[dict(name="_TEXT", cls="CODE", data=bytes(data), align=1)],
            publics=[("E4_Mut", 1, 0)], whole_ledata=True)

    clean = omf.parse_module(module(code))[0]
    scan = x.scan_slice(clean, db, prog, 0, len(code), CODE_BASE)
    assert scan.issues == []
    assert scan.instructions == 2

    changed = bytearray(code)
    changed[2] ^= 0xFF                              # non-address immediate byte
    scan = x.scan_slice(omf.parse_module(module(changed))[0], db, prog, 0,
                        len(code), CODE_BASE)
    finding, = [i for i in scan.issues if "compiled byte differs" in i["message"]]
    assert finding["reason"] == x.UNSUPPORTED
    assert finding["offset"] == 2

    proof = VerifiedRegion(candidate=CandidateRegion(0, len(code), CODE_BASE),
                           orig_end=CODE_BASE + len(code),
                           entries=((0, "E4_Mut"),), leading_size=0,
                           trailing_filler_size=0, obligations=(), data_deps=(),
                           outgoing_refs=(), verification_scope="extracted_slice",
                           evidence_digest="self-check")
    with pytest.raises(x.UnsupportedExtractionError) as excinfo:
        x.extract(module(changed), proof, db, prog)
    assert excinfo.value.reason == x.UNSUPPORTED
    assert "compiled byte differs from the verified original" in \
        excinfo.value.record["message"]
    assert excinfo.value.record["offset"] == 2
    assert excinfo.value.record["got"] == changed[2]
    assert excinfo.value.record["want"] == code[2]

    packed, prov = x.extract(module(code), proof, db, prog)
    assert prov["invariants"] == dict(region_match=True, byte_invariant=True,
                                      non_relocated_bytes=len(code), relocated_fields=0)
    assert bytes(omf.parse_module(packed)[0].seg("_TEXT")[1].data) == code


def test_chunk_planner_never_splits_a_fixup_field():
    def fix(offset):
        return x.RawFix(offset, x.LOC32, False, 5, None, 2, 1, None)

    assert x.CHUNK == 1024
    assert x._chunks(2048, []) == [(0, 1024), (1024, 2048)]
    # A field straddling a cut pulls the cut back to its first byte.
    assert x._chunks(1500, [fix(1022)]) == [(0, 1022), (1022, 1500)]
    assert x._chunks(3000, [fix(1022)]) == [(0, 1022), (1022, 2046), (2046, 3000)]
    assert x._chunks(3000, [fix(2046)]) == [(0, 1024), (1024, 2046), (2046, 3000)]
    # A boundary exactly at the field start or end is legal.
    assert x._chunks(1024, [fix(1020)]) == [(0, 1024)]
    assert x._chunks(1024, [fix(1024)]) == [(0, 1024)]


def test_thread_definitions_expand_into_self_contained_fixups():
    """FIXUPP32 THREAD slots are resolved; emission never depends on them."""
    def index(n):
        return bytes([0x80 | (n >> 8), n & 0xFF]) if n >= 128 else bytes([n])

    body = bytearray()
    body += bytes([0x40 | (5 << 2) | 0])            # F0: frame method 5 (Target)
    body += bytes([(2 << 2) | 0]) + index(130)      # T0: target method 2, EXTDEF 130
    body += (0x8000 | (9 << 10) | 1020).to_bytes(2, "big")  # loc 9, self-relative
    body += bytes([0x80 | (0 << 4) | 0x08 | 0])     # use both slots, explicit disp
    body += struct.pack("<I", 4)

    fixes = x.Threads().parse(bytes(body), 4)
    assert len(fixes) == 1
    fix = fixes[0]
    assert fix.as_dict() == dict(offset=1020, loc=9, self_rel=True, frame_method=5,
                                 frame_index=None, target_method=2, target_index=130,
                                 displacement=4)
    assert [f.as_dict() for f in x.Threads().parse(fix.encode(), 4)] == [fix.as_dict()]

    undefined = (0x8000 | (9 << 10) | 1020).to_bytes(2, "big") + b"\x88" + \
        struct.pack("<I", 0)
    with pytest.raises(x.UnsupportedExtractionError, match="undefined THREAD"):
        x.Threads().parse(undefined, 4)
    with pytest.raises(x.UnsupportedExtractionError, match="truncated FIXUPP"):
        x.Threads().parse(bytes([0x44]), 4)


def test_record_checksums_and_modend_are_enforced():
    from wc1.omfpatch import _pack

    code = b"\xC3"
    raw = builder.build(segments=[dict(name="_TEXT", cls="CODE", data=code, align=1)],
                        publics=[("E4_End", 1, 0)])
    assert [t for t, _ in x.read_records(raw)][-1] == 0x8A
    broken = bytearray(raw)
    broken[4] ^= 1
    with pytest.raises(x.UnsupportedExtractionError, match="bad OMF checksum"):
        x.read_records(bytes(broken))
    without_end = b"".join(_pack(t, body) for t, body in x.read_records(raw)[:-1])
    with pytest.raises(x.UnsupportedExtractionError, match="missing MODEND"):
        x.read_records(without_end)


def test_loadable_digest_ignores_compiler_facing_metadata():
    """THEADR and COMENT do not change the loadable identity."""
    from wc1.omfpatch import _pack

    case = fixtures.mutable_data()
    base = x.loadable_digest(case["mod"])
    records = x.read_records(case["obj"])
    renamed = [(0x80, bytearray(b"\x1f" + b"e4 renamed module" + b"x" * 14))] + \
        [record for record in records if record[0] != 0x80]
    commented = [(0x88, bytearray(b"\x00e4 comment"))] + renamed
    for variant in (renamed, commented):
        raw = b"".join(_pack(t, body) for t, body in variant)
        assert x.loadable_digest(omf.parse_module(raw)[0]) == base
    different = omf.parse_module(builder.build(
        segments=[dict(name="_TEXT", cls="CODE", data=b"\xC3", align=1)],
        publics=[("E4_Other", 1, 0)]))[0]
    assert x.loadable_digest(different) != base
