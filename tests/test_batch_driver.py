"""Unit tests for wc1.batch_driver (ledger, budget caps, TOML/evidence sanitization, dry-run)."""
import os

import pytest

from wc1 import batch_driver, path


def test_ledger_tracks_cost_and_cache_hit(tmp_path):
    lg = batch_driver.Ledger(str(tmp_path / "l.jsonl"))
    lg.record("claude_call", label="c1", cost_usd=0.10, usage={
        "input_tokens": 10, "cache_creation_input_tokens": 4000,
        "cache_read_input_tokens": 0, "output_tokens": 500,
    })
    lg.record("claude_call", label="c2", cost_usd=0.04, usage={
        "input_tokens": 10, "cache_creation_input_tokens": 500,
        "cache_read_input_tokens": 3500, "output_tokens": 400,
    })
    # Reload from disk
    lg2 = batch_driver.Ledger(str(tmp_path / "l.jsonl"))
    s = lg2.summary()
    assert s["calls"] == 2
    assert abs(s["cost_usd"] - 0.14) < 1e-6
    assert s["cache_read_tokens"] == 3500
    assert s["cache_hit_pct"] > 40.0


def test_budget_cap_blocks_before_calling_claude(tmp_path):
    lg = batch_driver.Ledger(str(tmp_path / "cap.jsonl"))
    lg.record("claude_call", label="c1", cost_usd=1.25, usage={})
    with pytest.raises(batch_driver.BudgetExceededError):
        batch_driver.call_claude("hi", {}, str(tmp_path / "sys.txt"),
                                 ledger=lg, max_cost=1.00)


def test_sanitize_evidence_strips_ghidra():
    ev = batch_driver._sanitize_evidence([
        "Ghidra decompiler shows loop",
        "calls SndPlay (0x26958) at 0x1b8a7",
    ])
    assert len(ev) == 1
    assert "ghidra" not in ev[0].lower()


def test_batch_driver_dry_run():
    if not os.path.exists(path("original", "install", "war.exe")):
        pytest.skip("needs original/install/war.exe")
    rc = batch_driver.run_full_module("mod_2b8e0", dry_run=True)
    assert rc == 0


def test_pytest_output_rejects_all_skipped():
    assert not batch_driver._pytest_output_passed(0, "8 skipped in 0.12s")
    assert not batch_driver._pytest_output_passed(1, "3 passed, 1 failed")
    assert not batch_driver._pytest_output_passed(0, "5 passed, 1 xfailed in 0.45s")
    assert not batch_driver._pytest_output_passed(0, "5 passed in 0.45s", test_src="@pytest.mark.xfail\ndef test_a(): pass")
    assert batch_driver._pytest_output_passed(0, "8 passed in 0.45s")


def test_pick_nonclobber_test_rel():
    # test_network.py exists -> must pick a non-clobbering _batch name
    rel = batch_driver._pick_nonclobber_test_rel("network")
    assert rel != "tests/test_network.py"
    assert rel.startswith("tests/test_network_batch")
    assert batch_driver._pick_nonclobber_test_rel("nonexistent_area_xyz") == "tests/test_nonexistent_area_xyz.py"


def test_ledger_last_stage_and_drafted_files_keyed_by_addr(tmp_path):
    lg = batch_driver.Ledger(str(tmp_path / "l.jsonl"))
    lg.record("target_addrs", addrs=["0x1000", "0x1010", "0x1020"])
    lg.record("draft_b0", files=2, files_map={"0x1000": "src/a/f0.c", "0x1010": "src/a/f1.c"})
    lg.record("draft_b1", files=1, files_map={"0x1020": "src/a/f2.c"})
    lg2 = batch_driver.Ledger(str(tmp_path / "l.jsonl"))
    assert lg2.last_stage("target_addrs")["addrs"] == ["0x1000", "0x1010", "0x1020"]
    assert lg2.drafted_files() == {
        0x1000: "src/a/f0.c",
        0x1010: "src/a/f1.c",
        0x1020: "src/a/f2.c",
    }


def test_find_forbidden_test_cheat_and_pytest_output_strict():
    std_mark = (
        "pytestmark = pytest.mark.skipif("
        "not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), "
        "reason='needs original/ and $WATCOM')\n"
    )
    assert batch_driver.find_forbidden_test_cheat(std_mark + "def test_ok():\n    assert 1\n") is None
    assert batch_driver.find_forbidden_test_cheat("def test_s():\n    pytest.skip('missing')\n") is not None
    assert batch_driver.find_forbidden_test_cheat("@pytest.mark.skipif(True, reason='x')\ndef test_s(): pass\n") is not None
    assert batch_driver.find_forbidden_test_cheat("pytestmark = pytest.mark.skip(reason='all')\n") is not None
    assert batch_driver.find_forbidden_test_cheat("@pytest.mark.xfail\ndef test_x(): pass\n") is not None
    # Partial skips (the test_snd_f1.py bug) MUST be rejected
    assert not batch_driver._pytest_output_passed(0, "2 passed, 2 skipped in 0.45s")
    assert batch_driver._pytest_output_passed(0, "2 passed in 0.45s", test_src=std_mark)


def test_verify_t4_node_checks_ref_file_and_skips(tmp_path):
    tdir = tmp_path / "tests"
    tdir.mkdir()
    good = tdir / "test_demo.py"
    good.write_text(
        "def test_foo():\n"
        "    # t4spec.run_spec('src/demo/foo_reference.c', ...)\n"
        "    assert True\n"
        "def test_skip():\n"
        "    import pytest\n"
        "    pytest.skip('not present')\n"
    )
    # File has inline pytest.skip -> rejected even for test_foo
    ok_cheat, reason_cheat = batch_driver.verify_t4_node(
        "difftest: tests/test_demo.py::test_foo", ref_rel="src/demo/foo_reference.c", cwd=str(tmp_path),
    )
    assert not ok_cheat and "cheat" in reason_cheat

    clean = tdir / "test_clean.py"
    clean.write_text(
        "def test_foo():\n"
        "    src = 'src/demo/foo_reference.c'\n"
        "    _ = 't4spec.run_spec'\n"
        "    assert src.endswith('_reference.c')\n"
        "def test_wrong_src():\n"
        "    src = 'src/demo/bar.c'\n"
        "    _ = 't4spec.run_spec'\n"
        "    assert src\n"
    )
    ok1, r1 = batch_driver.verify_t4_node(
        "difftest: tests/test_clean.py::test_foo", ref_rel="src/demo/foo_reference.c", cwd=str(tmp_path),
    )
    assert ok1, r1
    # Wrong ref filename (like fn_26360.c instead of fn_26360_reference.c) -> rejected
    ok2, r2 = batch_driver.verify_t4_node(
        "difftest: tests/test_clean.py::test_wrong_src", ref_rel="src/demo/bar_reference.c", cwd=str(tmp_path),
    )
    assert not ok2 and "bar_reference.c" in r2
    # Missing node -> rejected
    ok3, _ = batch_driver.verify_t4_node(
        "difftest: tests/test_clean.py::test_nonexistent", ref_rel="src/demo/foo_reference.c", cwd=str(tmp_path),
    )
    assert not ok3


def test_is_protected_toml_blocks_codegen_promo_and_untracked(tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    sdir = tmp_path / "analysis" / "symbols"
    sdir.mkdir(parents=True)
    (sdir / "tracked.toml").write_text("# ok\n")
    (sdir / "codegen_promo.toml").write_text("# locked\n")
    (sdir / "bullet.toml").write_text("# untracked wip\n")
    subprocess.run(["git", "add", "analysis/symbols/tracked.toml", "analysis/symbols/codegen_promo.toml"],
                   cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    assert batch_driver._is_protected_toml("analysis/symbols/codegen_promo.toml", cwd=str(tmp_path))
    assert batch_driver._is_protected_toml("analysis/symbols/bullet.toml", cwd=str(tmp_path))
    assert not batch_driver._is_protected_toml("analysis/symbols/tracked.toml", cwd=str(tmp_path))
    assert not batch_driver._is_protected_toml(
        "analysis/symbols/new_area.toml", created_rel="analysis/symbols/new_area.toml", cwd=str(tmp_path),
    )


def test_addrs_frozen_mismatch_and_ineligible(tmp_path, monkeypatch):
    if not os.path.exists(path("original", "install", "war.exe")):
        pytest.skip("needs original/install/war.exe")
    # 0x110a0 is data-in-code; passing it via --addrs must exit EXIT_NOTHING_TO_DO without fallback
    lg_dir = tmp_path / "ledger"
    lg_dir.mkdir()
    orig_path = batch_driver.path
    monkeypatch.setattr(
        batch_driver, "path",
        lambda *parts: os.path.join(str(tmp_path), *parts[1:]) if parts and parts[0] == "build" and len(parts) > 1 and parts[1] == "ledger" else orig_path(*parts),
    )
    rc = batch_driver.run_full_module("mod_110a0", area="test_inelig", addrs="0x110a0", dry_run=True)
    assert rc == batch_driver.EXIT_NOTHING_TO_DO

    # Resumed ledger with mismatched --addrs must exit EXIT_ADDR_MISMATCH
    lg = batch_driver.Ledger(str(lg_dir / "test_mismatch.jsonl"))
    lg.record("target_addrs", addrs=["0x1d7cc"])
    rc2 = batch_driver.run_full_module("INIT.C", area="test_mismatch", addrs="0x1d7cc,0x1d800", dry_run=True)
    assert rc2 == batch_driver.EXIT_ADDR_MISMATCH


def test_build_check_t3_buildable_detects_interior_refs(tmp_path):
    if not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")):
        pytest.skip("needs original/ and $WATCOM")
    from wc1 import analysis, build, match, symbols
    p = analysis.run()
    funcs_db, _, _ = symbols.load(strict=False)
    # InitPaths (0x1d7cc) IS buildable
    init_src = "src/init.c"
    init_obj = str(tmp_path / "init.obj")
    match.compile_c(path(init_src), None, init_obj, cc=match.file_cc(path(init_src)))
    ok_init, reason_init = build.check_t3_buildable(p, funcs_db, init_src, init_obj, [funcs_db[0x1d7cc]])
    assert ok_init, reason_init
    # SelectionClickUnit (0x2efd0) has an interior branch from 0x2f0b9 -> NOT buildable
    scu_src = "src/mod_2efd0/selection_click_unit.c"
    scu_obj = str(tmp_path / "scu.obj")
    match.compile_c(path(scu_src), None, scu_obj, cc=match.file_cc(path(scu_src)))
    ok_scu, reason_scu = build.check_t3_buildable(p, funcs_db, scu_src, scu_obj, [funcs_db[0x2efd0]])
    assert not ok_scu and "cannot replace" in reason_scu


def test_build_check_t3_buildable_detects_out_of_order_anchors_despite_patched_build_obj(tmp_path, monkeypatch):
    """Even when build/obj/ holds omfpatch-emptied objects from `make build`,
    `check_t3_buildable` must see real unpatched data anchors of existing `src =` files."""
    if not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")):
        pytest.skip("needs original/ and $WATCOM")
    from wc1 import analysis, build, symbols
    p = analysis.run()
    funcs_db, _, _ = symbols.load(strict=False)
    # Minimal funcs_db containing one real anchored T3 file: DefeatDialog @ 0x1ab28 (CONST @ 0x56c0c)
    defeat_e = funcs_db[0x1ab28]
    mini_db = {0x1ab28: defeat_e}
    # Force a fresh cache path in tmp_path so we exercise the real unpatched compile path
    orig_path = build.path
    monkeypatch.setattr(
        build, "path",
        lambda *parts: os.path.join(str(tmp_path), *parts) if parts and parts[0] == "build" else orig_path(*parts),
    )
    # Candidate placed BEFORE 0x1ab28 in code (0x104b0) but anchored AFTER 0x56c0c in data (0x572b4) -> out of order!
    real_place = build.place

    def fake_place(prog, src, obj, funcs):
        if src == "src/fake/early_code_late_data.c":
            return (0x104b0, 0x104c0), [(0x572b4, "CONST")]
        return real_place(prog, src, obj, funcs)

    monkeypatch.setattr(build, "place", fake_place)
    cand = {"addr": 0x104b0, "name": "FakeEarly", "link_name": "FakeEarly_"}
    ok, reason = build.check_t3_buildable(p, mini_db, "src/fake/early_code_late_data.c", "", [cand])
    assert not ok and "data anchors are not in code order" in reason

