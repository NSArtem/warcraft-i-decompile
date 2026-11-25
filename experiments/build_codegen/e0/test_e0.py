"""E0 controls run against the real installed compilers and supplied EXE."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import pytest
from wc1 import analysis, symbols
from .controls import build_controls, evaluate_control
from .matcher_proto import OriginalIndex
from .reaudit_t3 import CATEGORIES, RESULTS, VERDICTS, discover


@pytest.fixture(scope="module")
def results():
    cases = build_controls()
    indexes = {id(c.p): OriginalIndex(c.p) for c in cases}
    return {c.id: evaluate_control(c, indexes[id(c.p)]) for c in cases}


IDS = ["P1", "N1", "P2", "N2", "P3", "P4", "N3", "N4", "N5", "P5", "N6", "N7", "N8",
       "B_grp", "B_frame", "B_data_self_rel", "B_leading_reverse", "B_intra_rel32",
       "B_intra_rel8", "B_external_hardcoded_rel32", "B_extent_filler", "B_extent_fixup",
       "B_extent_overlap", "B_data_to_text", "B_data_chain", "B_debug_metadata", "B_unanchored_data",
       "B_data_location", "B_data_frame", "B_unknown_location", "B_wrong_addend", "B_leading_byte",
       "B_public_disagreement", "B_prefixed_branch", "B_data_bytes_match", "B_data_byte_corrupt"]
IDS += ["R1_truncated_ret", "R1_truncated_instruction", "R2_trimmed_rel8", "R2_trimmed_rel32",
        "R2_trimmed_rel32_fixup", "R2_sibling_trimmed_rel32", "R3_metadata_publics",
        "R3_metadata_statics", "R3_conflicting_publics", "R3_conflicting_statics",
        "R3_local_chain_publics", "R3_local_chain_statics", "R4_extra_code",
        "R5_oob_end", "R5_oob_negative", "R3_unreferenced_publics", "R3_unreferenced_statics",
        "R3_transitive_publics", "R3_transitive_statics"]


@pytest.mark.parametrize("cid", IDS)
def test_control(results, cid):
    assert results[cid]["passed"], results[cid]


@pytest.mark.parametrize("cid", ["N1", "N2", "N3", "N4", "B_leading_reverse",
                               "B_external_hardcoded_rel32"])
def test_legacy_false_matches(results, cid):
    assert results[cid]["legacy_verdict"] == "MATCH"
    assert results[cid]["e0_region_verdict"] == "MISMATCH"


def test_multi_finding_is_exhaustive(results):
    row = results["N8"]
    cats = {f["category"] for f in row["findings"]}
    assert {"code_bytes", "code_reloc_reverse", "data_reloc_forward"} <= cats
    assert len(row["findings"]) >= 3
    for f in row["findings"]:
        assert {"code", "category", "offset", "orig_addr", "message", "evidence"} <= f.keys()


@pytest.mark.parametrize("cid", ["R1_truncated_ret", "R1_truncated_instruction",
                               "R2_trimmed_rel8", "R2_trimmed_rel32", "R2_trimmed_rel32_fixup"])
def test_truncated_bodies_and_reachable_tails_never_match(results, cid):
    assert results[cid]["e0_region_verdict"] != "MATCH"
    assert results[cid]["e0_function_verdicts"]
    assert all(v != "MATCH" for v in results[cid]["e0_function_verdicts"])


def test_earlier_function_uses_final_region_extent(results):
    row = results["R2_sibling_trimmed_rel32"]
    assert row["e0_region_verdict"] == "MISMATCH"
    assert row["e0_function_verdicts"] == ["MISMATCH", "MATCH"]


@pytest.mark.parametrize("entrypoint", ["run_e0", "reaudit_t3"])
@pytest.mark.parametrize("scope", ["function_verdicts", "region_verdicts", None])
def test_entrypoint_exit_on_either_audit_error(monkeypatch, tmp_path, entrypoint, scope):
    import importlib
    module = importlib.import_module("."+entrypoint, __package__)
    summary = dict(count_matches_expectation=True,
                   function_verdicts={"ERROR": int(scope == "function_verdicts")},
                   region_verdicts={"ERROR": int(scope == "region_verdicts")})
    monkeypatch.setattr(module, "audit", lambda *args: dict(summary=summary))
    if entrypoint == "run_e0":
        monkeypatch.setattr(module, "run_controls", lambda: dict(total=0, passed=0, failed=0))
    monkeypatch.setattr("sys.argv", [entrypoint, "--output", str(tmp_path)])
    assert module.main() == int(scope is not None)


def test_real_leading_and_hardware_metrics(results):
    assert results["P1"]["metrics"]["leading_bytes_len"] == 16
    assert results["P3"]["findings"] == []
    assert results["P3"]["metrics"]["reverse_le_fixups_checked"] == 0
    assert results["P4"]["metrics"]["data_fixups_checked"] == 2


def test_saved_controls_reproduce(results):
    saved = json.loads((RESULTS / "controls.json").read_text())
    assert saved["failed"] == 0
    assert saved["total"] == saved["passed"] == len(results)
    assert {r["id"]: r for r in saved["controls"]} == json.loads(json.dumps(results))


def test_full_audit_inventory_and_evidence():
    saved = json.loads((RESULTS / "t3_reaudit.json").read_text())
    funcs, _, _ = symbols.load()
    expected = discover(analysis.run(), funcs)
    rows = saved["functions"]
    assert len(rows) == len(expected) == 519
    assert len({r["src"] for r in rows}) == 514
    assert len({r["addr"] for r in rows}) == len(rows)
    assert {int(r["addr"], 16) for r in rows} == {r["addr"] for r in expected}
    assert saved["provenance"]["production_diff"] == ""
    prototype = Path(__file__).with_name("matcher_proto.py")
    assert saved["provenance"]["prototype_sha256"] == hashlib.sha256(prototype.read_bytes()).hexdigest()
    for key, field in (("function_verdicts", "e0_function_verdict"),
                       ("region_verdicts", "e0_region_verdict")):
        counts = Counter(r[field] for r in rows)
        assert set(counts) <= set(VERDICTS)
        assert saved["summary"][key] == {v: counts[v] for v in VERDICTS}
    counts = Counter(r["rfc15_category"] for r in rows)
    assert set(counts) <= set(CATEGORIES)
    assert saved["summary"]["rfc15_categories"] == {v: counts[v] for v in CATEGORIES}
    obligation_fields = {"kind", "src_offset", "field_size", "target", "addend", "evaluation_rule",
                         "requires_static_resolution", "requires_le_fixup"}
    for r in rows:
        assert r["obj_sha256"] and len(r["obj_sha256"]) == 64
        assert all(obligation_fields <= o.keys() for o in r["normalized_obligations"])
    with (RESULTS / "t3_reaudit.csv").open(newline="") as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == len(rows)
    for csv_row, row in zip(csv_rows, rows):
        assert csv_row["addr"] == row["addr"]
        assert json.loads(csv_row["findings"]) == row["findings"]
