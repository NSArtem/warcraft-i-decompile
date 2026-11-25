"""E0 controls run against the real installed compilers and supplied EXE."""
import pytest
from .controls import build_controls, evaluate_control
from .matcher_proto import OriginalIndex


@pytest.fixture(scope="module")
def results():
    cases = build_controls()
    indexes = {id(c.p): OriginalIndex(c.p) for c in cases}
    return {c.id: evaluate_control(c, indexes[id(c.p)]) for c in cases}


IDS = ["P1", "N1", "P2", "N2", "P3", "P4", "N3", "N4", "N5", "P5", "N6", "N7", "N8",
       "B_grp", "B_frame", "B_data_self_rel", "B_leading_reverse", "B_intra_rel32",
       "B_intra_rel8", "B_external_hardcoded_rel32", "B_extent_filler", "B_extent_fixup",
       "B_extent_overlap", "B_data_to_text", "B_data_chain"]


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
