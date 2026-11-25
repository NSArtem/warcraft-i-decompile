"""E8 test suite: artifact reproducibility, corpus integrity, no circular truth.

Run from the repository root:

    pytest -q experiments/build_codegen/e8/test_e8.py

The heavy inputs are cached under `build/e8/` by `python3 -m
experiments.build_codegen.e8.run_e8`; tests that need a cache rebuild it (the
synthetic corpus takes a few seconds, the libsig sweep is skipped when its
cache is absent).
"""
import copy
import csv
import json
import re
from pathlib import Path

import pytest

from wc1 import path

from experiments.build_codegen.e8 import (EXPERIMENT, RESULTS, SCHEMA, SCRATCH,
                                          sha256_file)
from experiments.build_codegen.e8 import evaluate_signals as ev
from experiments.build_codegen.e8 import real_corpus, run_e8, synthetic_corpus

JSON_ARTIFACTS = ("synthetic_manifest.json", "metrics.json", "game_exploratory.json")
CSV_ARTIFACT = "signal_metrics.csv"
SIGNALS = [name for name, _role in ev.SIGNALS]
SPLIT = {name for name, role in ev.SIGNALS if role == ev.SPLIT}
MERGE = {name for name, role in ev.SIGNALS if role == ev.MERGE}
# Signals that are computable for every pair; the string-window/staircase rules
# need data references and `flag_set_S_disjoint` needs a measured S(f).
ALWAYS_EVALUABLE = {"zero16", "zero4", "zero2", "none16", "style_transition",
                    "call_locality_drop", "non_16_aligned_start", "shared_epilogue",
                    "shared_const_string_literal", "exclusive_static_data_sharing",
                    "call_locality_link"}


def artifact(name):
    return RESULTS / name


def read_json(name):
    return json.loads(artifact(name).read_text(encoding="utf-8"))


def have_war():
    return Path(path("original", "install", "war.exe")).is_file()


needs_war = pytest.mark.skipif(not have_war(), reason="war.exe is user-supplied original data")
needs_libsig_cache = pytest.mark.skipif(not (SCRATCH / "libsig10a.json").is_file(),
                                        reason="run_e8 has not built the libsig cache")


# ---------------------------------------------------------------------------
# artifacts: existence, canonical serialization, LF, path freedom
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", JSON_ARTIFACTS)
def test_json_artifacts_are_canonical(name):
    p = artifact(name)
    assert p.is_file(), f"{name} missing"
    text = p.read_text(encoding="utf-8")
    assert json.loads(text) is not None
    assert text == json.dumps(json.loads(text), sort_keys=True, indent=2) + "\n", \
        f"{name} is not canonical sort_keys/indent JSON"


def test_csv_is_lf_and_canonical():
    p = artifact(CSV_ARTIFACT)
    raw = p.read_bytes()
    assert b"\r" not in raw, "CSV must use LF line terminators"
    assert raw.endswith(b"\n")
    with open(p, encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == ["corpus", "signal", "role", "TP", "FP", "TN", "FN", "precision",
                       "recall", "F1", "sample_size", "unavailable", "classification"]
    assert {r[0] for r in rows[1:]} == {"synthetic", "libsig", "setup"}
    assert {r[1] for r in rows[1:]} == set(SIGNALS)


PATHLIKE = re.compile(r"(/mnt/|/home/|/tmp/|/nix/|[A-Za-z]:\\\\|wc1e7-|build/e8|"
                      r"\d{4}-\d{2}-\d{2}T\d{2}:)")


@pytest.mark.parametrize("name", JSON_ARTIFACTS + (CSV_ARTIFACT,))
def test_artifacts_are_path_and_time_free(name):
    text = artifact(name).read_text(encoding="utf-8")
    bad = PATHLIKE.search(text)
    assert bad is None, f"{name} contains host-specific text {bad.group(0)!r}"


def test_metrics_declares_scope_and_schema():
    m = read_json("metrics.json")
    assert m["schema"] == SCHEMA and m["experiment"] == EXPERIMENT
    assert set(m["corpora"]) == {"synthetic", "libsig", "setup"}
    assert "exploratory" in m["ground_truth_rule"]
    assert "never" in m["ground_truth_rule"]["exploratory"].lower()
    assert m["determinism"]["paths_recorded"] is False
    assert m["determinism"]["corpus_a_labels_from_recipe_membership"] is True
    assert m["determinism"]["corpus_b1_labels_from_object_identity"] is True
    assert m["determinism"]["corpus_b2_labels_from_setup_provenance"] is True


def test_every_contract_signal_has_a_metric_on_every_corpus():
    m = read_json("metrics.json")
    for cid in ("synthetic", "libsig", "setup"):
        block = m["corpora"][cid]
        names = {s["signal"] for s in block["signals"]}
        assert names == set(SIGNALS), f"{cid}: {set(SIGNALS) - names}"
        for s in block["signals"]:
            for key in ("TP", "FP", "TN", "FN", "sample_size", "unavailable",
                        "precision", "recall", "F1", "classification"):
                assert key in s
            assert s["sample_size"] == s["TP"] + s["FP"] + s["TN"] + s["FN"]
            assert s["role"] in (ev.SPLIT, ev.MERGE)
        # the signals the contract names must actually be evaluable on a corpus
        # that has both truth classes
        if block["sample"]["same_cu"] and block["sample"]["boundaries"]:
            for name in ALWAYS_EVALUABLE:
                s = next(x for x in block["signals"] if x["signal"] == name)
                assert s["sample_size"] > 0, f"{cid}: {name} has no sample"
        for name in ({"const_window_break", "data_bss_staircase_break",
                      "const_window_continues", "data_staircase_continues"}
                     - ALWAYS_EVALUABLE):
            s = next(x for x in block["signals"] if x["signal"] == name)
            assert s["sample_size"] + s["unavailable"] == block["sample"]["pairs"]


# ---------------------------------------------------------------------------
# corpus A: designed coverage and recipe-only ground truth
# ---------------------------------------------------------------------------
def test_manifest_covers_the_contract_edge_cases():
    man = read_json("synthetic_manifest.json")
    d = man["designed_cases"]["checks"]
    assert d["boundaries"] >= 15 and d["same_cu_pairs"] >= 30
    assert d["zero16_boundaries"] >= 5                 # PARA-aligned CUs with 1..15 zero bytes
    assert d["zero4_boundaries"] >= 1 and d["zero2_boundaries"] >= 1
    assert d["none16_boundaries"] >= 2                 # _TEXT a multiple of 16: no padding
    assert d["data16_boundaries"] >= 1                 # in-code data before the first function
    assert d["same_cu_none16_candidates"] >= 1         # 16-aligned interior start, same CU
    assert d["same_cu_zero16_candidates"] >= 1         # zero fill inside a hand-written module
    assert d["same_cu_zero4_candidates"] >= 1
    styles = {cu["flags"] for cu in man["cus"] if cu["kind"] == "c"}
    for needle in ("-4r", "-5r", "-3r", "-os", "-od", "-d1+", "-oa"):
        assert any(needle in f for f in styles), f"missing style {needle}"
    kinds = [cu["kind"] for cu in man["cus"]]
    assert kinds.count("asm") >= 3 and kinds.count("c") >= 15
    # the corpus must be big enough for the contract's 15-20 CUs / 60-80 functions
    assert 15 <= len(man["cus"]) <= 30
    assert 60 <= len(man["functions"]) <= 90


def test_synthetic_labels_are_recipe_membership_not_signals():
    man = read_json("synthetic_manifest.json")
    funcs = man["functions"]
    want = [(i, "boundary" if funcs[i - 1]["cu"] != funcs[i]["cu"] else "same_cu")
            for i in range(1, len(funcs))]
    got = [(lab["i"], lab["truth"]) for lab in man["labels"]]
    assert got == want


def test_scrambling_every_evaluated_feature_does_not_change_truth():
    """The ground truth must not be a function of the signals (Mandatory R4)."""
    man = read_json("synthetic_manifest.json")
    original = [(lab["i"], lab["truth"]) for lab in man["labels"]]
    scrambled = copy.deepcopy(man)
    scrambled["ranges"] = {"const": [[0, 1]], "data": [[0, 1]]}
    for f in scrambled["functions"]:
        f["S"] = []
    for lab in scrambled["labels"]:
        lab["rule"], lab["gap_kind"], lab["gap_len"] = "even", "made-up", 99
    assert [(lab["i"], lab["truth"]) for lab in scrambled["labels"]] == original


def test_synthetic_corpus_rebuilds_byte_identically():
    corpus = synthetic_corpus.build(force=True)
    man = read_json("synthetic_manifest.json")
    assert corpus["image"]["text_sha256"] == man["image"]["text_sha256"]
    assert corpus["spec_sha256"] == man["provenance"]["spec_sha256"]
    assert [cu["id"] for cu in corpus["cus"]] == [cu["id"] for cu in man["cus"]]


def test_sf_sets_are_measured_and_contain_the_cu_own_configuration():
    man = read_json("synthetic_manifest.json")
    cfgs = {c["id"]: c["flags"] for c in man["configurations"]}
    from experiments.build_codegen.e7.common import CORE_FLAGS
    assert len(cfgs) == len(CORE_FLAGS) == 22
    assert set(cfgs) == {f"c{k:02d}" for k in range(1, len(CORE_FLAGS) + 1)}
    by_id = {cu["id"]: cu for cu in man["cus"]}
    checked = 0
    for f in man["functions"]:
        cu = by_id[f["cu"]]
        assert isinstance(f["S"], list)
        if cu["kind"] == "asm":
            assert f["S"] == []          # the flag signal does not apply to asm
            continue
        own = next(cid for cid, flags in cfgs.items() if flags == cu["flags"])
        assert own in f["S"], f"{f['name']}: own configuration {own} not in S(f)"
        checked += 1
    assert checked >= 55


# ---------------------------------------------------------------------------
# corpus B: independent labels
# ---------------------------------------------------------------------------
@needs_war
@needs_libsig_cache
def test_libsig_labels_come_from_object_identity():
    prog = real_corpus.war_program()
    corp = real_corpus.libsig_corpus(prog)
    extents = {(c["lib"], c["module"], c["segi"]): (c["start"], c["end"]) for c in corp["cus"]}
    assert len(extents) >= 50
    for lab in corp["labels"]:
        cov_a = {k for k, (lo, hi) in extents.items() if lo <= lab["prev"] < hi}
        cov_b = {k for k, (lo, hi) in extents.items() if lo <= lab["cur"] < hi}
        assert cov_a and cov_b
        assert ("library object" in lab["evidence"]) or ("->" in lab["evidence"])
        if lab["truth"] == "same_cu":
            assert cov_a & cov_b
        else:
            assert not (cov_a & cov_b)
    m = read_json("metrics.json")["corpora"]["libsig"]
    assert m["sample"]["boundaries"] >= 40 and m["sample"]["same_cu"] >= 100
    assert m["provenance"]["matcher"] == "wc1.clib_sig"


@needs_war
def test_setup_labels_come_from_setup_provenance():
    if not Path(path("original", "install", "setup.exe")).is_file():
        pytest.skip("setup.exe is not supplied")
    prog = real_corpus.war_program()
    corp = real_corpus.setup_corpus(prog)
    assert len(corp["labels"]) >= 20
    for lab in corp["labels"]:
        assert lab["truth"] == "boundary"          # boundary-only corpus
        assert "identical" in lab["evidence"]
        assert not re.search(r"zero|padding|staircase|style", lab["evidence"])
    m = read_json("metrics.json")["corpora"]["setup"]
    assert m["sample"]["same_cu"] == 0 and m["sample"]["boundaries"] >= 20
    # precision must be reported as unmeasurable, never as a perfect score
    for s in m["signals"]:
        assert s["precision"] is None
        assert s["precision_measurable"] is False


# ---------------------------------------------------------------------------
# measured conclusions that the report relies on
# ---------------------------------------------------------------------------
def test_zero16_recall_gap_is_quantified():
    m = read_json("metrics.json")["corpora"]["synthetic"]["signals"]
    z = next(s for s in m if s["signal"] == "zero16")
    n = next(s for s in m if s["signal"] == "none16")
    assert z["TP"] >= 5
    assert z["FN"] >= 4               # exact-16-multiple and byte-aligned boundaries
    assert n["TP"] >= 2               # hidden none16 boundaries are detected only by the baseline
    assert z["precision"] is not None and z["recall"] is not None


@needs_war
@needs_libsig_cache
def test_padding_rules_do_not_transfer_to_byte_aligned_library_objects():
    lib = read_json("metrics.json")["corpora"]["libsig"]["signals"]
    z = next(s for s in lib if s["signal"] == "zero16")
    assert z["recall"] < 0.10, "zero16 recall on library objects should be poor"
    assert z["precision"] < 0.90, "zero16 precision on library objects should be poor"
    narrow = [next(s for s in lib if s["signal"] == n) for n in ("zero4", "zero2")]
    assert all(s["precision"] == 1.0 for s in narrow if s["TP"])


def test_shared_epilogue_is_precise_on_the_synthetic_corpus():
    syn = read_json("metrics.json")["corpora"]["synthetic"]["signals"]
    epi = next(s for s in syn if s["signal"] == "shared_epilogue")
    assert epi["TP"] >= 2 and epi["FP"] == 0
    assert epi["precision"] == 1.0


@needs_war
@needs_libsig_cache
def test_shared_epilogue_is_precise_on_real_library_objects():
    lib = read_json("metrics.json")["corpora"]["libsig"]["signals"]
    epi = next(s for s in lib if s["signal"] == "shared_epilogue")
    assert epi["TP"] >= 3 and epi["FP"] == 0


def test_designed_false_positives_are_reported_for_every_noisy_signal():
    syn = read_json("metrics.json")["corpora"]["synthetic"]["signals"]
    for name in ("zero16", "zero4", "none16", "data_bss_staircase_break",
                 "non_16_aligned_start", "exclusive_static_data_sharing"):
        s = next(x for x in syn if x["signal"] == name)
        assert s["FP"] >= 1, f"{name} should have a designed false positive"
        assert s["examples"]["false_positives"]


def test_game_analysis_is_labeled_exploratory_and_separate():
    g = read_json("game_exploratory.json")
    assert g["caveat"].startswith("EXPLORATORY")
    assert "never" in g["caveat"] or "nothing here" in g["caveat"]
    m = read_json("metrics.json")
    for block in m["corpora"].values():
        assert "game_exploratory.json" not in json.dumps(block)
    assert g["functions_in_range"] > 500
    assert len(g["candidate_none16_splits"]) >= 10
    assert "S_f_provenance" in g and "reconstructed TU context" in g["S_f_provenance"]["caveat"]
    names = {c["chunk"] for c in g["chunks"]}
    for named in ("mod_13f60", "mod_16390", "STATUS.C"):
        assert any(named in n for n in names), f"{named} missing from the chunk table"
    starts = {c["start"] for c in g["chunks"]}
    for addr in (0x13f60, 0x16390, 0x1f050, 0x27b20):
        assert addr in starts, f"chunk at {addr:#x} missing"
    assert any(c["start"] == 0x1f050 for c in g["highlighted_chunks"])


# ---------------------------------------------------------------------------
# end-to-end reproducibility from the caches
# ---------------------------------------------------------------------------
def test_run_e8_regenerates_the_committed_artifacts_byte_identically():
    if not (SCRATCH / "corpus.json").exists():
        pytest.skip("run_e8 has not built the synthetic corpus cache")
    before = {name: artifact(name).read_bytes() for name in JSON_ARTIFACTS + (CSV_ARTIFACT,)}
    run_e8.run(verbose=False)
    after = {name: artifact(name).read_bytes() for name in JSON_ARTIFACTS + (CSV_ARTIFACT,)}
    differing = [name for name in before if before[name] != after[name]]
    if differing:                      # keep the tree canonical for the next test run
        for name in differing:
            artifact(name).write_bytes(before[name])
    assert not differing, f"non-deterministic artifacts: {differing}"
