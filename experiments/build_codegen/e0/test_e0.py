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
