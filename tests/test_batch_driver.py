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
    assert batch_driver._pytest_output_passed(0, "8 passed in 0.45s")
    assert batch_driver._pytest_output_passed(0, "5 passed, 1 xfailed in 0.45s")


def test_pick_nonclobber_test_rel():
    # test_network.py exists -> must pick a non-clobbering _batch name
    rel = batch_driver._pick_nonclobber_test_rel("network")
    assert rel != "tests/test_network.py"
    assert rel.startswith("tests/test_network_batch")
    assert batch_driver._pick_nonclobber_test_rel("nonexistent_area_xyz") == "tests/test_nonexistent_area_xyz.py"

