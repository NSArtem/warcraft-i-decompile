"""Tests for campaign runner infrastructure hardening (limits, TMPDIR, resume, verdict safety)."""
import json
import os
import subprocess
import pytest

from experiments.build_codegen._infra import run_agent


def test_default_timeouts_by_role():
    assert run_agent.default_timeout_for_role("reviewer") == 1800
    assert run_agent.default_timeout_for_role("developer") == 2700
    with pytest.raises(ValueError):
        run_agent.default_timeout_for_role("unknown")


def test_effective_prompt_appends_deadline_and_rules():
    eff = run_agent._build_effective_prompt(
        "Base prompt",
        role="reviewer",
        timeout_s=1800,
        start_epoch=1795638000,
        start_utc="2026-11-25T20:20:00Z",
    )
    assert "Base prompt" in eff
    assert "2026-11-25T20:20:00Z" in eff
    assert "`1800 s`" in eff
    assert "`1260 s`" in eff  # 70% checkpoint
    assert "date -u +%s" in eff
    assert "No `sleep`" in eff or "Do NOT use `sleep`" in eff
    assert "make verify" in eff
    assert "Batch independent" in eff


def test_session_tmpdir_is_short_unique_and_created():
    d1 = run_agent._make_session_tmpdir("rev-e8-02")
    d2 = run_agent._make_session_tmpdir("rev-e8-02")
    d3 = run_agent._make_session_tmpdir("very-long-session-identifier-exceeding-limit-999")
    try:
        assert d1.startswith("/tmp/wc1-")
        assert len(d1) <= 32
        assert len(d3) <= 32
        assert d1 != d2
        assert os.path.isdir(d1) and os.path.isdir(d2) and os.path.isdir(d3)
    finally:
        for d in (d1, d2, d3):
            if os.path.isdir(d):
                os.rmdir(d)


def test_verdict_safety_fail_closed_on_timeout():
    # Earlier turn mentions APPROVE in prose, final message has no explicit VERDICT: line -> None!
    combined = "I will check whether to APPROVE or REJECT this branch.\nStill checking fixtures."
    final_msg = "Still checking fixtures; maybe APPROVE later."
    assert run_agent._extract_verdict(combined, final_message=final_msg, timed_out=True) is None

    # Explicit VERDICT: line in an EARLIER turn, NOT final message -> still None on timeout!
    assert run_agent._extract_verdict(
        "VERDICT: APPROVE\nWait, actually running more tests",
        final_message="Running more tests...",
        timed_out=True,
    ) is None

    # Explicit VERDICT: line IN final message -> extracted cleanly (even with markdown formatting)
    assert run_agent._extract_verdict(
        combined + "\n1. **VERDICT: REQUEST_CHANGES**\n",
        final_message="Summary:\n1. **VERDICT: REQUEST_CHANGES**\nUnchecked: item X",
        timed_out=True,
    ) == "REQUEST_CHANGES"

    # Clean non-timed-out completion accepts explicit VERDICT line
    assert run_agent._extract_verdict(
        "All checks passed.\nVERDICT: APPROVE\n",
        final_message="All checks passed.\nVERDICT: APPROVE\n",
        timed_out=False,
    ) == "APPROVE"


def test_git_dirty_state_ignores_original_symlink(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("hi\n")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    os.symlink("/tmp", tmp_path / "original")

    st = run_agent._git_dirty_state(str(tmp_path))
    assert st["is_dirty"] is False
    assert st["untracked"] == []

    (tmp_path / "untracked.py").write_text("x = 1\n")
    (tmp_path / "a.txt").write_text("changed\n")
    st2 = run_agent._git_dirty_state(str(tmp_path))
    assert st2["is_dirty"] is True
    assert "untracked.py" in st2["untracked"]
    assert any("a.txt" in m for m in st2["modified"])


def test_opencode2_timeout_triggers_single_resume_and_aggregates_telemetry(tmp_path, monkeypatch):
    # Set up isolated git worktree + fake state/telemetry dirs
    wt = tmp_path / "wt"
    wt.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=wt, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=wt, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=wt, check=True)
    (wt / "base.txt").write_text("base\n")
    subprocess.run(["git", "add", "base.txt"], cwd=wt, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=wt, check=True)

    state_root = tmp_path / "state"
    tel_dir = tmp_path / "tel"
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("Review E99.")

    monkeypatch.setattr(run_agent, "STATE_ROOT", str(state_root))
    monkeypatch.setattr(run_agent, "TELEMETRY_DIR", str(tel_dir))
    monkeypatch.setattr(run_agent, "MAIN_REPO", str(tmp_path))

    events = []
    monkeypatch.setattr(run_agent, "write_event", lambda et, pay: events.append((et, pay)))
    monkeypatch.setattr(run_agent, "log_decision", lambda *a, **kw: None)
    monkeypatch.setattr(run_agent, "log_termination", lambda *a, **kw: None)

    calls = []

    def fake_run(cmd, *, cwd, env, stdout_path, stderr_path, timeout_s, stdin_bytes=None):
        calls.append({"cmd": cmd, "cwd": cwd, "tmpdir": env["TMPDIR"], "wineprefix": env["WINEPREFIX"], "timeout_s": timeout_s})
        assert os.path.isdir(env["TMPDIR"])
        assert env["TMPDIR"].startswith("/tmp/wc1-")
        if len(calls) == 1:
            # Initial call times out mid-work (note bare APPROVE word in prose must NOT be accepted!)
            with open(stdout_path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps({"type": "text", "sessionID": "ses_test_123", "part": {"text": "Checking whether to APPROVE..."}}) + "\n")
                fh.write(json.dumps({"type": "step_finish", "sessionID": "ses_test_123", "part": {"tokens": {"input": 100, "output": 20, "reasoning": 50, "cache": {"read": 1000}}}}) + "\n")
            return 124, True, 1800.0
        else:
            # Resume call uses -s ses_test_123 and returns an explicit VERDICT: REQUEST_CHANGES
            assert "-s" in cmd and "ses_test_123" in cmd
            with open(stdout_path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps({"type": "text", "sessionID": "ses_test_123", "part": {"text": "VERDICT: REQUEST_CHANGES\nUnchecked: test Z"}}) + "\n")
                fh.write(json.dumps({"type": "step_finish", "sessionID": "ses_test_123", "part": {"tokens": {"input": 30, "output": 15, "reasoning": 10, "cache": {"read": 1100}}}}) + "\n")
            return 0, False, 12.5

    monkeypatch.setattr(run_agent, "_run_subprocess_bounded", fake_run)

    rc = run_agent.run_opencode2_session(
        session_id="rev-test-01",
        exp_id="E99",
        role="reviewer",
        task_id="test-timeout-resume",
        worktree=str(wt),
        branch="detached-test",
        prompt_file=str(prompt_file),
        model="opencode-go/deepseek-v4.1-flash",
    )

    assert rc == 124
    assert len(calls) == 2
    assert calls[0]["timeout_s"] == 1800
    assert calls[1]["timeout_s"] == 300
    assert calls[0]["tmpdir"] == calls[1]["tmpdir"]
    assert not os.path.exists(calls[0]["tmpdir"])  # cleaned up after resume!
    assert calls[0]["wineprefix"].endswith("build/oldcc/wineprefix")

    sess_events = [pay for et, pay in events if et == "agent_session"]
    assert len(sess_events) == 1
    rec = sess_events[0]
    assert rec["task_status"] == "TIMED_OUT"
    assert rec["timed_out"] is True
    assert rec["initial_wall_s"] == 1800.0
    assert rec["wall_s"] == 1812.5
    assert rec["input_tokens"] == (100 + 1000) + (30 + 1100)
    assert rec["cached_input_tokens"] == 2100
    assert rec["output_tokens"] == 35
    assert rec["reasoning_tokens"] == 60
    assert rec["turns"] == 2
    assert rec["review_verdict"] == "REQUEST_CHANGES"
    assert rec["resume"]["attempted"] is True
    assert rec["resume"]["succeeded"] is True
    assert rec["resume"]["raw_jsonl_path"].endswith("rev-test-01.resume.jsonl")
    assert os.path.isfile(rec["resume"]["raw_jsonl_path"])
