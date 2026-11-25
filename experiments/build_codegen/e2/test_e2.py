"""E2 regression checks: fresh compiles, real E0 positive/negative controls,
inventory completeness, exhaustive per-function accounting, and artifact parity.
"""
from collections import Counter
from copy import deepcopy
import csv
import json
from pathlib import Path
import sys

# pytest's console entry point supplies tools/ via PYTHONPATH but does not
# put the repository's namespace-package root on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pytest
from wc1 import analysis
from experiments.build_codegen.e0.matcher_proto import OriginalIndex
from .harness import (FLAGS, HERE, RESULTS, ROOT, SCRATCH, VARIANTS, body_evidence,
    compile_source, consolidate, evaluate, header_overlay, inventory, sha,
    starts, summary, wilson)
from .synthetic import MATRIX, call_source, layout, loop_source, loops, pooling_literals, snapshot


@pytest.fixture(scope="module")
def saved():
    if not (RESULTS / "results.json").exists():
        # Commit 1's harness is independently runnable before saved empirical
        # outputs arrive in commit 2. Generate evidence, never skip assertions.
        from .run_e2 import main
        previous = sys.argv
        try:
            sys.argv = ["run_e2"]
            assert main() == 0
        finally:
            sys.argv = previous
    return json.loads((RESULTS / "results.json").read_text())


@pytest.fixture(scope="module")
def original():
    entries, excluded, db = inventory()
    p = analysis.run(cache=False)
    return p, OriginalIndex(p), entries, db


@pytest.mark.parametrize(("cc", "variant", "offsets", "segdef_align"), [
    ("10.0a", "cpu3", [0, 8, 20, 40], 3),
    ("10.0a", "native", [0, 16, 32, 64], 3),
    ("10.0a", "cpu5", [0, 8, 20, 40], 3),
    ("ow2", "cpu3", [0, 8, 20, 40], 3),
    ("ow2", "native", [0, 16, 32, 64], 3),
    ("ow2", "cpu5", [0, 16, 32, 64], 3),
    ("10.0a", "size", [0, 5, 16, 33], 1),
    ("10.0a", "cpu3_size", [0, 5, 16, 33], 1),
    ("10.0a", "cpu5_size", [0, 5, 16, 33], 1),
    ("10.0a", "od", [0, 25, 56, 93], 1),
])
def test_fresh_exact_length_alignment(cc, variant, offsets, segdef_align):
    mod = compile_source(HERE / "fixtures/alignment.c", MATRIX[variant],
                         f"test/alignment_{cc}_{variant}", cc)
    by_name = {r["name"]: r for r in layout(mod)["functions"]}
    probes = [by_name[f"Body{n}_"] for n in (5, 11, 17, 23)]
    assert [body["start"] for body in probes] == offsets
    assert mod.seg("_TEXT")[1].align == segdef_align
    for n, body in zip((5, 11, 17, 23), probes):
        assert body["body_size"] == n + (20 if variant == "od" else 0)
        assert body["padding_is_filler"]
        if segdef_align == 1:
            assert body["padding_hex"] == ""


def test_fresh_pooling_and_static_storage():
    mod = compile_source(HERE / "fixtures/pooling.c", FLAGS, "test/pooling")
    a = body_evidence(mod, "PoolA_")
    b = body_evidence(mod, "PoolB_")
    assert a["neutral_hex"] == b["neutral_hex"]
    assert a["fixups"][0]["inline_addend"] == b["fixups"][0]["inline_addend"]
    assert a["fixups"][0]["target"] == b["fixups"][0]["target"]
    assert any(s.name == "_DATA" and s.length >= 8 for s in mod.segments)


def test_const_snapshot_preserves_literals_and_masks_padding(saved):
    row = next(r for r in saved["synthetic"]["matrix"] if
               (r["compiler"], r["variant"], r["fixture"]) == ("10.0a", "native", "pooling"))
    mod = compile_source(HERE / "fixtures/pooling.c", FLAGS, "test/pooling_padding")
    literals, gaps = pooling_literals(mod, row["data_references"])
    assert [(r["offset"], bytes.fromhex(r["hex"])) for r in literals] == [
        (0, b"E2-identical\0"), (16, b"a\0"), (20, b"bc\0"), (24, b"defg\0")]
    assert literals == row["const_literals"]
    assert row["const_padding_gaps"] == [
        dict(offset=13, length=3), dict(offset=18, length=2), dict(offset=23, length=1)]
    original = snapshot(mod, gaps)
    assert json.loads(json.dumps(original)) == row["omf"]

    _, const = mod.seg("CONST")
    for gap in gaps:
        offset = gap["offset"]
        fill = 0 if gap["nonzero"] else 255
        const.data[offset:offset+gap["length"]] = bytes([fill]) * gap["length"]
    changed_literals, changed_gaps = pooling_literals(mod, row["data_references"])
    assert changed_literals == literals
    assert [g["nonzero"] for g in changed_gaps] == [not g["nonzero"] for g in gaps]
    assert snapshot(mod, changed_gaps) == original


def test_loop_probe_has_real_back_edges():
    src = SCRATCH / "test_loop.c"
    src.write_text(loop_source(3))
    mod = compile_source(src, FLAGS, "test/loop")
    evidence = loops(mod)
    assert len(evidence) == 2
    assert all(r["back_edges"] for r in evidence)
    assert all(bytes.fromhex(r["body_hex"]).count(b"\x90") >= 3 for r in evidence)


def test_tail_fixup_does_not_make_alignment_padding_reachable(original):
    _, _, entries, _ = original
    ee = [e for e in entries if e["name"] in ("OpenGameMenu", "CanCancelConstruction")]
    alone = next(e for e in ee if e["name"] == "OpenGameMenu")
    a = compile_source(Path(alone["src"]), FLAGS, "test/tail_alone")
    src = consolidate(ee, SCRATCH / "test_tail.c")
    b = compile_source(src, FLAGS, "test/tail_tu")
    first = body_evidence(a, "OpenGameMenu_")
    second = body_evidence(b, "OpenGameMenu_")
    assert first["body_size"] == second["body_size"] == 10
    assert first["instruction_sha256"] == second["instruction_sha256"]


@pytest.mark.parametrize("variant", ["native", "cpu5", "size"])
def test_static_global_extern_register_control(variant):
    bodies = []
    for kind in ("static", "global", "extern"):
        src = SCRATCH / ("test_call_"+kind+".c")
        src.write_text(call_source(kind))
        mod = compile_source(src, VARIANTS[variant], "test/call_"+variant+kind)
        bodies.append(body_evidence(mod, "Caller_"))
    assert len({b["instruction_sha256"] for b in bodies}) == 1
    assert len({json.dumps(b["calls"]) for b in bodies}) == 1


def test_neighbor_only_shift_does_not_inject_instruction_bytes():
    observed = []
    for prefix in (0, 4, 8, 12):
        src = SCRATCH / f"test_shift_{prefix}.c"
        src.write_text(loop_source(prefix, internal_prefix=False))
        mod = compile_source(src, VARIANTS["cpu5"], "test/shift_"+str(prefix))
        observed.append(body_evidence(mod, "LoopFor_"))
    assert len({r["start"] for r in observed}) > 1
    assert len({r["instruction_sha256"] for r in observed}) == 1


def test_real_e0_region_and_corruption_controls(original):
    p, idx, entries, db = original
    # These five leaf mask predicates are contiguous in the original and
    # have 16-byte original spacings; this is an actual multi-function TU.
    names = {"CanBuildRoad", "CanBuildWall", "CanTrainConjurer", "CanTrainCleric", "CanBuildLumberMill"}
    ee = [e for e in entries if e["name"] in names]
    assert len(ee) == 5
    src = consolidate(ee, SCRATCH / "test_region.c")
    mod = compile_source(src, FLAGS, "test/region")
    positive = evaluate(p, idx, db, mod)
    assert positive["region"]["verdict"] == "MATCH"
    assert all(f["verdict"] == "MATCH" for f in positive["functions"].values())
    bad = deepcopy(mod)
    # Corruption is a test negative control only, never a study object.
    bad.seg("_TEXT")[1].data[0] ^= 1
    assert evaluate(p, idx, db, bad)["region"]["verdict"] != "MATCH"
    bad = deepcopy(mod)
    bad.seg("_TEXT")[1].fixups.clear()
    rejected = evaluate(p, idx, db, bad)
    assert rejected["region"]["verdict"] != "MATCH"
    assert any(f["code"] == "missing_compiled_absolute_fixup" for f in rejected["region"]["findings"])


def test_status_requires_only_declaration_overlay(original):
    p, idx, entries, db = original
    ee = [e for e in entries if e["area"] == "status"]
    src = consolidate(ee, SCRATCH / "test_status.c")
    with pytest.raises(SystemExit, match="E1151"):
        compile_source(src, FLAGS, "test/status_stale")
    overlay, evidence = header_overlay()
    assert len(evidence["declarations"]) == 5
    mod = compile_source(src, FLAGS, "test/status_corrected", overlay=overlay)
    assert {n for _, n in starts(mod)} == {e["link_name"] for e in ee}


def test_inventory_is_complete_and_baselines_match(saved):
    entries, excluded, _ = inventory()
    assert saved["selection"] == entries
    assert saved["excluded"] == excluded
    assert Counter(e["area"] for e in entries) == dict(gamedlg=14, playflic=24, status=58)
    assert len({e["src"] for e in entries}) == 96
    assert all(b["function"]["verdict"] == "MATCH" for b in saved["consolidation"]["baseline"])
    assert len(saved["consolidation"]["overlay_controls"]) == 58
    assert all(b["identical_body"] for b in saved["consolidation"]["overlay_controls"])
    assert saved["provenance"]["production_diff"] == ""
    assert saved["provenance"]["e0_matcher_sha256"] == sha((HERE.parent / "e0/matcher_proto.py").read_bytes())


def test_every_function_every_context_is_accounted_for(saved):
    rows = saved["consolidation"]["rows"]
    keys = {(r["group"], r["variant"], r["name"]) for r in rows}
    assert len(keys) == len(rows)
    for group in saved["consolidation"]["groups"]:
        selected = [r for r in rows if r["group"] == group["id"] and r["variant"] == group["variant"]]
        assert {r["name"] for r in selected} == set(group["names"])
        for k, v in summary(selected).items():
            assert group["summary"][k] == v
    for area in ("gamedlg", "playflic", "status"):
        for variant in VARIANTS:
            assert sum(r["group"] == area+"_all" and r["variant"] == variant for r in rows) == {
                "gamedlg": 14, "playflic": 24, "status": 58}[area]
    for r in rows:
        assert r["context_body_changed"] == (r["body"]["instruction_sha256"] != r["standalone_body"]["instruction_sha256"])
        if r["function"] != "MATCH":
            assert r["causes"] and r["e0_function"]["finding_counts"]
        if r["context_body_changed"]:
            assert r["context_first_difference"] is not None


def test_csv_exactly_tracks_json(saved):
    rows = saved["consolidation"]["rows"]
    assert b"\r" not in (RESULTS / "consolidation_rows.csv").read_bytes()
    with (RESULTS / "consolidation_rows.csv").open(newline="") as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == len(rows)
    for a, b in zip(csv_rows, rows):
        for key in a:
            if isinstance(b[key], (list, dict)):
                assert json.loads(a[key]) == b[key]
            elif b[key] is None:
                assert a[key] == ""
            else:
                assert a[key] == str(b[key])


def test_results_omit_checkout_paths_and_debug_contents(saved):
    data = (RESULTS / "results.json").read_text()
    for root in {str(ROOT), str(ROOT.resolve())}:
        for spelling in (root, root.replace("/", "\\")):
            assert json.dumps(spelling)[1:-1] not in data
            assert spelling.encode().hex() not in data
    synthetic_objects = saved["synthetic"]["matrix"] + saved["synthetic"]["calls"]
    synthetic_debug = [s for r in synthetic_objects for s in r["omf"]["segments"]
                       if s["name"] in {"$$TYPES", "$$SYMBOLS"}]
    assert synthetic_debug
    assert all(s["debug_metadata"] and s["length"] > 0 and
               "hex" not in s and "fixups" not in s for s in synthetic_debug)
    real_debug = [s for g in saved["consolidation"]["groups"] for s in g["segments"]
                  if s["name"] in {"$$TYPES", "$$SYMBOLS"}]
    assert real_debug
    assert all(s["debug_metadata"] and s["size"] > 0 and
               "sha256" not in s for s in real_debug)


def test_perturbation_controls_are_region_matches_and_byte_lengths_measured(saved):
    pp = saved["perturbations"]
    assert len({r["group"] for r in pp}) >= 2
    assert all(r["control_region"] == "MATCH" for r in pp)
    for group in {r["group"] for r in pp}:
        rr = [r for r in pp if r["group"] == group]
        assert {r["kind"] for r in rr} == {"bytes_1", "bytes_2", "bytes_3", "bytes_7", "string", "pressure", "epilogue"}
        for row in rr:
            assert len(row["neighbors"]) == len(row["names"])-1
            if row["kind"].startswith("bytes_"):
                assert row["edited_body_size_delta"] == int(row["kind"].split("_")[1])


def test_synthetic_matrix_is_complete(saved):
    matrix = saved["synthetic"]["matrix"]
    for flag in ("-3r", "-4r", "-5r", "-ot", "-os", "-od", "-d1+", "-ol", "-oa", "-or"):
        assert any(flag in r["flags"].split() and r["compiler"] == "10.0a" for r in matrix)
    assert {r["variant"] for r in matrix if r["compiler"] == "ow2"} == {"native", "cpu5"}
    loop_rows = saved["synthetic"]["loops"]
    for cc, variant in {(r["compiler"], r["variant"]) for r in loop_rows}:
        assert {r["prefix_bytes"] for r in loop_rows if (r["compiler"], r["variant"]) == (cc, variant)} == set(range(16))


def test_wilson_describes_only_observed_sample():
    assert wilson(0, 0) is None
    lo, hi = wilson(96, 96)
    assert 0.96 < lo < 1 and hi == 1
    lo, hi = wilson(0, 96)
    assert lo == 0 and 0 < hi < 0.04
