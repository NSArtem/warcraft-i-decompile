"""E8 test suite: artifact reproducibility, corpus integrity, no circular truth.

Run from the repository root:

    pytest -q experiments/build_codegen/e8/test_e8.py

The heavy inputs are cached under `build/e8/` by `python3 -m
experiments.build_codegen.e8.run_e8`; the session fixture below populates that
cache from the recipe and the user-supplied binaries, so a fresh checkout runs
every test (the synthetic corpus takes a few seconds, the libsig sweep is paid
once and cached on the input digests).  Tests skip only when a user-supplied
input (`war.exe`, `setup.exe`, the 10.0a libraries) is genuinely absent.
"""
import copy
import csv
import json
import re
from pathlib import Path

import pytest

from wc1 import analysis, oldcc, path

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


def have_setup():
    return Path(path("original", "install", "setup.exe")).is_file()


def have_libs():
    return Path(oldcc.root(), "lib386", "dos", "clib3r.lib").is_file()


needs_war = pytest.mark.skipif(not have_war(), reason="war.exe is user-supplied original data")


@pytest.fixture(scope="session", autouse=True)
def e8_caches():
    """Populate `build/e8` so a fresh checkout runs every test (rev-e8-02 F3).

    Corpus A is a recipe build (a few seconds); the B1/B2 sweeps are cached on
    the digests of the user-supplied binaries, so the first run on a fresh
    checkout pays for them once instead of skipping every dependent test.
    Only a genuinely absent input leaves tests skipped.
    """
    corpus = synthetic_corpus.build()
    if not (have_war() and have_libs()):
        return corpus
    prog = real_corpus.war_program()
    real_corpus.libsig_corpus(prog)
    if have_setup():
        real_corpus.setup_corpus(prog)
    return corpus


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


def test_synthetic_data_digest_is_padding_independent(tmp_path, monkeypatch):
    """rev-e8-02 F1: wcc386 leaves its CONST alignment padding uninitialized.

    The committed manifest must therefore carry a padding-normalized data
    digest, and a rebuild in a different directory (different compiler heap
    contents, different pad bytes) must reproduce it.
    """
    man = read_json("synthetic_manifest.json")
    assert "data_sha256" not in man["image"]
    census = man["image"]["data_padding_normalized"]
    assert census["padding_bytes"] > 0 and census["gaps"]
    cached = synthetic_corpus.build()
    assert cached["image"]["semantic_data_sha256"] == man["image"]["semantic_data_sha256"]
    monkeypatch.setattr(synthetic_corpus, "SCRATCH", tmp_path)
    other = synthetic_corpus.build(force=True)
    assert other["image"]["text_sha256"] == man["image"]["text_sha256"]
    assert other["image"]["semantic_data_sha256"] == man["image"]["semantic_data_sha256"]
    assert other["image"]["data_padding_normalized"] == census


def test_data_digest_excludes_only_the_compiler_padding_gaps():
    """The normalization is exactly the pad bytes: nothing else is dropped."""
    corpus = synthetic_corpus.build()
    man = read_json("synthetic_manifest.json")
    prog = analysis.Program(corpus["_exe"])
    mapinfo = synthetic_corpus.parse_map(
        (Path(SCRATCH) / "e8synth.map").read_text(encoding="utf-8"))
    raw = bytes(prog.image[analysis.DATA_OBJ])
    canon, census = synthetic_corpus.semantic_data(prog, mapinfo)
    assert census == man["image"]["data_padding_normalized"]
    assert len(canon) == len(raw)
    gaps = {k for off, n in census["gaps"] for k in range(off, off + n)}
    assert len(gaps) == census["padding_bytes"] > 0
    for value in (0x00, 0x11, 0x7E, 0xA5):
        noisy = bytearray(raw)
        for off, n in census["gaps"]:
            noisy[off:off + n] = bytes([value]) * n
        assert synthetic_corpus.semantic_data(prog, mapinfo, bytes(noisy))[0] == canon, \
            f"pad value {value:#04x} changed the data digest"
    covered = 0
    for k in range(len(raw)):
        if k in gaps:
            continue
        noisy = bytearray(raw)
        noisy[k] ^= 0xFF
        try:
            changed = synthetic_corpus.semantic_data(prog, mapinfo, bytes(noisy))[0] != canon
        except RuntimeError:
            changed = True          # a damaged declared literal is rejected outright
        assert changed, f"data byte {k:#x} is not covered by the digest"
        covered += 1
    assert covered >= 150


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
def test_every_admitted_b1_extent_passes_full_segment_masked_verification():
    """A single library-function signature hit is not enough (rev-e8-01)."""
    from wc1 import clib_sig, oldcc

    prog = real_corpus.war_program()
    corp = real_corpus.libsig_corpus(prog)
    mods = {(lib, m.name): m for lib, m in clib_sig.load_modules(oldcc.root())}
    assert corp["cus"]
    for cu in corp["cus"]:
        ok, reason, detail = real_corpus.verify_extent(
            prog, cu["lib"], cu["module"], cu["segi"], cu["start"])
        assert ok, f"{cu['id']} at {cu['start']:#x}: {reason} {detail}"
        assert detail["bytes"] > 0
        assert cu["end"] == cu["start"] + detail["bytes"], cu["id"]
        # Independent re-check of the bytes and absolute relocations.
        seg = mods[(cu["lib"], cu["module"])].segments[cu["segi"] - 1]
        assert len(seg.data) == detail["bytes"]
        mask = bytearray(len(seg.data))
        for f in seg.fixups:
            n = min(f.size, len(seg.data) - f.offset)
            mask[f.offset:f.offset + n] = b"\x01" * n
        o0 = cu["start"] - prog.code.base
        assert all(mask[k] or seg.data[k] == prog.cbytes[o0 + k]
                   for k in range(len(seg.data))), cu["id"]
        for f in seg.fixups:
            if not f.self_rel:
                assert (cu["start"] + f.offset) in prog.fix_at, cu["id"]


@needs_war
def test_admitted_b1_extents_do_not_overlap():
    prog = real_corpus.war_program()
    corp = real_corpus.libsig_corpus(prog)
    cus = sorted(corp["cus"], key=lambda c: (c["start"], c["end"]))
    for a, b in zip(cus, cus[1:]):
        assert a["end"] <= b["start"], f"{a['id']} [{a['start']:#x},{a['end']:#x}) overlaps " \
                                       f"{b['id']} [{b['start']:#x},{b['end']:#x})"
    assert corp["diagnostics"]["overlap_conflicts"] == 0


@needs_war
def test_cstrtx32_is_rejected_and_pair_0x34850_0x34860_is_not_same_cu():
    """rev-e8-01: a lone `__exit_` hit in cstrtx32 extrapolated over cstrt386."""
    prog = real_corpus.war_program()
    corp = real_corpus.libsig_corpus(prog)
    assert not any(c["module"] == "cstrtx32" for c in corp["cus"])
    rejected = {(r["lib"], r["module"]): r for r in corp["diagnostics"]["rejected_extents"]}
    assert ("cstrtx3r", "cstrtx32") in rejected
    entry = rejected[("cstrtx3r", "cstrtx32")]
    assert entry["reason"] == "unmasked byte differs from war.exe"
    assert entry["detail"]["mismatched_bytes"] > 0
    ok, reason, detail = real_corpus.verify_extent(prog, "cstrtx3r", "cstrtx32", 1, 0x3464b)
    assert not ok and detail["mismatched_bytes"] > 0
    # `vsprintf` is the other partial object caught by the same rule: its
    # shared `mem_putc_` prefix matches but its `vsprintf_` body does not.
    assert ("clib3r", "vsprintf") in rejected
    assert rejected[("clib3r", "vsprintf")]["reason"] == \
        "unmasked byte differs from war.exe"
    # 0x34850 is inside the genuine cstrt386 object; 0x34860 is outside every
    # admitted extent, so the pair cannot receive a same-CU label.
    assert any(c["start"] <= 0x34850 < c["end"] for c in corp["cus"])
    assert not any(c["start"] <= 0x34860 < c["end"] for c in corp["cus"])
    assert not any(lab["prev"] == 0x34850 and lab["cur"] == 0x34860
                   for lab in corp["labels"] if lab["truth"] == "same_cu")
    assert not any(lab["prev"] == 0x34850 and lab["cur"] == 0x34860
                   for lab in corp["labels"])


@needs_war
def test_intxa386_is_verified_and_reported_as_a_sensitivity_run():
    prog = real_corpus.war_program()
    corp = real_corpus.libsig_corpus(prog)
    cu = next(c for c in corp["cus"] if c["module"] == "intxa386")
    ok, reason, detail = real_corpus.verify_extent(
        prog, cu["lib"], cu["module"], cu["segi"], cu["start"])
    assert ok, f"intxa386 should be a genuine object: {reason} {detail}"
    assert detail["bytes"] == 990
    m = read_json("metrics.json")
    full = m["corpora"]["libsig"]["sample"]
    sens = m["sensitivity"]["libsig_without_intxa386"]["sample"]
    assert full["dominant_extent"]["module"] == "clib3r:intxa386"
    assert full["dominant_extent"]["same_cu_pairs"] >= 250
    assert sens["excluded_modules"] == ["intxa386"]
    assert sens["pairs"] < full["pairs"] and sens["same_cu"] < full["same_cu"]
    assert full["same_cu"] - sens["same_cu"] >= 250
    assert sens["counts"]["admitted_extents"] == full["counts"]["admitted_extents"] - 1


@needs_war
@pytest.mark.skipif(not have_setup(), reason="setup.exe is user-supplied original data")
def test_setup_labels_come_from_setup_provenance():
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
def test_padding_rules_do_not_transfer_to_byte_aligned_library_objects():
    lib = read_json("metrics.json")["corpora"]["libsig"]["signals"]
    z = next(s for s in lib if s["signal"] == "zero16")
    assert z["recall"] < 0.10, "zero16 recall on library objects should be poor"
    # After rev-e8-01 removed the phantom cstrtx32 overlap, zero16 has only two
    # positives and no false positive; that is not strong evidence (TP < 5).
    assert z["TP"] <= 2 and z["FP"] == 0
    assert z["classification"] == "weak_ambiguous"
    narrow = [next(s for s in lib if s["signal"] == n) for n in ("zero4", "zero2")]
    assert all(s["precision"] == 1.0 for s in narrow if s["TP"])


def test_shared_epilogue_is_precise_on_the_synthetic_corpus():
    syn = read_json("metrics.json")["corpora"]["synthetic"]["signals"]
    epi = next(s for s in syn if s["signal"] == "shared_epilogue")
    assert epi["TP"] >= 2 and epi["FP"] == 0
    assert epi["precision"] == 1.0


@needs_war
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
    before = {name: artifact(name).read_bytes() for name in JSON_ARTIFACTS + (CSV_ARTIFACT,)}
    run_e8.run(verbose=False)
    after = {name: artifact(name).read_bytes() for name in JSON_ARTIFACTS + (CSV_ARTIFACT,)}
    differing = [name for name in before if before[name] != after[name]]
    if differing:                      # keep the tree canonical for the next test run
        for name in differing:
            artifact(name).write_bytes(before[name])
    assert not differing, f"non-deterministic artifacts: {differing}"
