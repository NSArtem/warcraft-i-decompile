"""Focused tests for the consilium orchestrator's resume/attempt bookkeeping.

These cover the administrative machinery only: an interrupted Architect must be
resumable without rerunning its peers, and every invocation of that Architect
must stay preserved side by side. Nothing here launches a provider session.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ORCH = pathlib.Path(__file__).resolve().parents[1] / (
    "docs/research/build-codegen-consilium/orchestrator/run_architect.py"
)
DEFAULT_CONSILIUM = pathlib.Path(
    "/mnt/data/projects/warcraft-1-decompile-wt/cons-sec/docs/research/build-codegen-consilium"
)


def load_orchestrator(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("consilium_run_architect", ORCH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    consilium = tmp_path / "consilium"
    (consilium / "rounds" / "r03").mkdir(parents=True)
    monkeypatch.setattr(mod, "CONSILIUM", str(consilium))
    return mod, consilium


def write_attempt(mod, consilium, arch, tag, status, sha):
    d = consilium / "rounds" / "r03" / arch / "attempts" / tag
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps({
        "round": "r03",
        "architect": arch,
        "attempt": tag,
        "status": status,
        "prompt_sha256": "p" * 64,
        "prompt_bytes": 10,
        "response_sha256": sha,
        "response_bytes": 20,
        "start_utc": "2026-11-27T00:00:00Z",
        "end_utc": "2026-11-27T00:01:00Z",
        "wall_s": 60.0,
        "exit_code": 0 if status == "COMPLETED" else 1,
        "api_error": None if status == "COMPLETED" else "usage_limit_reached",
        "session_id": "s",
    }), encoding="utf-8")


def test_attempt_index_keeps_failed_then_completed(monkeypatch, tmp_path):
    mod, consilium = load_orchestrator(monkeypatch, tmp_path)
    write_attempt(mod, consilium, "claude", "01-provider-rate-limit",
                  "PROVIDER_ERROR", "a" * 64)
    write_attempt(mod, consilium, "claude", "02-continuation", "COMPLETED", "b" * 64)

    index = mod.rebuild_attempt_index("r03", "claude")
    assert [a["attempt"] for a in index["attempts"]] == [
        "01-provider-rate-limit", "02-continuation"]
    assert index["of_record"] == "02-continuation"
    assert index["attempts"][0]["status"] == "PROVIDER_ERROR"
    # The failed invocation is preserved, not overwritten.
    assert index["attempts"][0]["response_sha256"] == "a" * 64
    on_disk = json.loads(
        (consilium / "rounds/r03/claude/attempts/index.json").read_text(encoding="utf-8"))
    assert on_disk == index


def test_attempt_index_has_no_record_until_success(monkeypatch, tmp_path):
    mod, consilium = load_orchestrator(monkeypatch, tmp_path)
    write_attempt(mod, consilium, "claude", "01-provider-rate-limit",
                  "PROVIDER_ERROR", "a" * 64)
    index = mod.rebuild_attempt_index("r03", "claude")
    assert index["of_record"] is None


def test_attempt_index_empty_without_attempts(monkeypatch, tmp_path):
    mod, _ = load_orchestrator(monkeypatch, tmp_path)
    index = mod.rebuild_attempt_index("r03", "claude")
    assert index["attempts"] == [] and index["of_record"] is None


def test_prompt_file_requires_exactly_one_architect(monkeypatch, tmp_path):
    mod, consilium = load_orchestrator(monkeypatch, tmp_path)
    prompt = consilium / "rounds/an.md"
    prompt.write_text("hello", encoding="utf-8")
    with pytest.raises(SystemExit):
        mod.launch_files("r03", 10, only=["claude", "gpt"], prompt_file=str(prompt))
    with pytest.raises(SystemExit):
        mod.launch_files("r03", 10, prompt_file=str(prompt))


def test_launch_files_rejects_unrendered_placeholders(monkeypatch, tmp_path):
    mod, consilium = load_orchestrator(monkeypatch, tmp_path)
    prompt = consilium / "rounds/an.md"
    prompt.write_text("deadline {{DEADLINE_UTC}}", encoding="utf-8")
    with pytest.raises(SystemExit):
        mod.launch_files("r03", 10, only=["claude"], prompt_file=str(prompt))


def test_live_orchestrator_keeps_three_named_architects():
    """Guard against a resume path silently changing an Architect's identity."""
    spec = importlib.util.spec_from_file_location("consilium_run_architect_live", ORCH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert {a: c["model_id"] for a, c in mod.ARCHITECTS.items()} == {
        "gpt": "gpt-6.2-sol",
        "claude": "claude-opus-5-5",
        "gemini": "gemini-4-neon-high",
    }
    assert {a: c["effort"] for a, c in mod.ARCHITECTS.items()} == {
        "gpt": "high", "claude": "high", "gemini": "high"}
