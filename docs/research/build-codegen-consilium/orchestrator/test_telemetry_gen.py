#!/usr/bin/env python3
"""Regression tests for the deterministic consilium telemetry generator.

Run with:  python3 -m pytest -q docs/research/build-codegen-consilium/orchestrator/test_telemetry_gen.py
"""

from __future__ import annotations

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CONSILIUM = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import telemetry_gen as tg  # noqa: E402


def test_real_campaign_counts_and_totals():
    out = tg.render(CONSILIUM)
    summary = json.loads(out["telemetry/summary.json"])
    claude = summary["architects"]["claude"]
    # 13 invocations: 11 completed, 2 provider-limit failures.
    assert claude["invocations"] == 13
    assert claude["completed"] == 11
    assert claude["failed"] == 2
    # Recorded input-token total at commit 6fa9e4b.
    assert claude["input_tokens_total"] == 107_265_151
    # One record per attempt: the failed R3 invocation is present once.
    rounds = [(d["round"], d["attempt"], d["status"]) for d in claude["cost_deltas"]]
    assert rounds.count(("r03", "01-provider-rate-limit", "PROVIDER_RATE_LIMIT")) == 1
    # editor-v3 is not double counted (round slot + attempt slot are the same invocation).
    assert sum(1 for r in rounds if r[0] == "editor-v3") == 1


def test_real_campaign_cost_deltas_are_chronological_and_positive():
    out = tg.render(CONSILIUM)
    summary = json.loads(out["telemetry/summary.json"])
    deltas = summary["architects"]["claude"]["cost_deltas"]
    # Sorted by real start time, cumulative cost strictly non-decreasing.
    starts = [d["start_utc"] for d in deltas]
    assert starts == sorted(starts)
    cums = [d["cumulative_cost_usd"] for d in deltas]
    assert cums == sorted(cums)
    by = {(d["round"], d["attempt"]): d["cost_delta_usd"] for d in deltas}
    assert by[("r03", "02-continuation")] == pytest.approx(9.04, abs=0.01)
    assert by[("approval", None)] == pytest.approx(1.31, abs=0.01)
    assert by[("editor-v3", "01-provider-rate-limit")] == pytest.approx(4.34, abs=0.01)
    assert all(d["cost_delta_usd"] >= 0 for d in deltas)


def test_gemini_cumulative_uncached_is_differenced():
    out = tg.render(CONSILIUM)
    import csv
    import io
    rows = list(csv.DictReader(io.StringIO(out["telemetry/resource-usage.csv"])))
    r01 = next(r for r in rows if r["round"] == "r01" and r["architect"] == "gemini")
    assert int(r01["uncached_input_tokens"]) == 397_557
    assert int(r01["cached_input_tokens"]) == 8_266_786


def test_cumulative_token_deltas_per_session():
    records = [
        {"architect": "gpt", "start_utc": "2026-01-01T00:00:00Z", "session_id": "s1",
         "usage": {"input_tokens": 100, "cached_input_tokens": 50, "output_tokens": 10,
                   "reasoning_tokens": 1}},
        {"architect": "gpt", "start_utc": "2026-01-01T01:00:00Z", "session_id": "s1",
         "usage": {"input_tokens": 250, "cached_input_tokens": 120, "output_tokens": 30,
                   "reasoning_tokens": 5}},
        # A different session restarts the cumulative counter.
        {"architect": "gpt", "start_utc": "2026-01-01T02:00:00Z", "session_id": "s2",
         "usage": {"input_tokens": 40, "cached_input_tokens": 10, "output_tokens": 4,
                   "reasoning_tokens": 0}},
    ]
    tg.annotate(records)
    got = [(r["usage_per_invocation"]["input_tokens"],
            r["usage_per_invocation"]["output_tokens"]) for r in records]
    assert got == [(100, 10), (150, 20), (40, 4)]


def test_negative_cost_delta_rejected():
    records = [
        {"architect": "claude", "start_utc": "2026-01-01T00:00:00Z", "session_id": "s1",
         "usage": {"total_cost_usd": 5.0}},
        {"architect": "claude", "start_utc": "2026-01-01T01:00:00Z", "session_id": "s1",
         "usage": {"total_cost_usd": 3.0}},
    ]
    with pytest.raises(ValueError, match="negative cumulative-cost delta"):
        tg.annotate(records)


def test_documented_provider_reset_allows_lower_counter():
    records = [
        {"architect": "claude", "start_utc": "2026-01-01T00:00:00Z", "session_id": "s1",
         "usage": {"total_cost_usd": 5.0}},
        {"architect": "claude", "start_utc": "2026-01-01T01:00:00Z", "session_id": "s1",
         "provider_counter_reset": True, "usage": {"total_cost_usd": 3.0}},
    ]
    tg.annotate(records)
    assert records[1]["usage_per_invocation"]["cost_delta_usd"] == pytest.approx(3.0)


def test_round_slot_duplicate_prefers_attempt_record(tmp_path):
    root = tmp_path / "rounds" / "rXX" / "claude"
    (root / "attempts" / "01-x").mkdir(parents=True)
    base = {"architect": "claude", "round": "rXX", "start_utc": "2026-01-01T00:00:00Z",
            "session_id": "s1", "usage": {"total_cost_usd": 1.0}, "status": "PROVIDER_ERROR"}
    (root / "meta.json").write_text(json.dumps(base))
    (root / "attempts" / "01-x" / "meta.json").write_text(json.dumps({**base, "attempt": "01-x"}))
    records = tg.collect(str(tmp_path))
    assert len(records) == 1
    assert records[0]["attempt"] == "01-x"
    assert records[0]["_from_attempts"] is True


def test_outputs_are_deterministic():
    assert tg.render(CONSILIUM) == tg.render(CONSILIUM)
