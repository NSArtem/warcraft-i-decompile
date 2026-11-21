"""Tests for wc1.live atomic IPC, tailer, stream-json parser, quota normalization,
and non-deadlocking call_claude streaming & process-tree timeout."""
import json
import os
import stat
import subprocess
import sys

import pytest

from wc1 import batch_driver, live


def test_parse_stream_json_line_variants():
    assert live.parse_stream_json_line("") is None
    assert live.parse_stream_json_line("{not json") is None

    th = live.parse_stream_json_line(json.dumps({
        "type": "stream_event",
        "event": {"type": "content_block_delta", "delta": {"type": "thinking_delta", "thinking": "checking regalloc"}},
    }))
    assert th == {"kind": "thinking_delta", "text": "checking regalloc"}

    tx = live.parse_stream_json_line(json.dumps({
        "type": "stream_event",
        "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "hello"}},
    }))
    assert tx == {"kind": "text_delta", "text": "hello"}

    ij = live.parse_stream_json_line(json.dumps({
        "type": "stream_event",
        "event": {"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": '{"a":1}'}},
    }))
    assert ij == {"kind": "input_json_delta", "text": '{"a":1}'}

    tu = live.parse_stream_json_line(json.dumps({
        "type": "stream_event",
        "event": {"type": "content_block_start", "content_block": {"type": "tool_use", "name": "Edit"}},
    }))
    assert tu == {"kind": "tool_use", "name": "Edit"}

    res = live.parse_stream_json_line(json.dumps({
        "type": "result", "structured_output": {"ok": True}, "total_cost_usd": 0.01,
    }))
    assert res["kind"] == "result"
    assert res["result"]["structured_output"] == {"ok": True}


def test_rate_limit_normalization_and_merge(tmp_path):
    ev = {
        "type": "rate_limit_event",
        "rate_limit_info": {
            "status": "allowed",
            "resetsAt": 1795224000,
            "rateLimitType": "five_hour",
            "unifiedWindows": {
                "five_hour": {"utilization": 0.41, "resetsAt": 1795224000, "status": "allowed"},
                "seven_day": {"utilization": 0.20, "resetsAt": 1795694400, "status": "allowed"},
            },
        },
    }
    parsed = live.parse_stream_json_line(json.dumps(ev))
    assert parsed["kind"] == "rate_limit"
    rl = parsed["rate_limit"]
    assert rl["five_hour"]["utilization"] == 0.41
    assert rl["five_hour"]["used_percentage"] == 41.0
    assert rl["seven_day"]["used_percentage"] == 20.0

    rl_file = str(tmp_path / "rate_limits.json")
    live.save_rate_limits(rl, fpath=rl_file)
    # Partial update only touching five_hour preserves seven_day
    live.save_rate_limits({
        "updated_at": 123.0,
        "status": "allowed",
        "five_hour": {"utilization": 0.55, "used_percentage": 55.0, "resets_at": 1795224000, "status": "allowed"},
    }, fpath=rl_file)
    loaded = live.load_rate_limits(fpath=rl_file)
    assert loaded["five_hour"]["used_percentage"] == 55.0
    assert loaded["seven_day"]["used_percentage"] == 20.0


def test_atomic_json_and_control_ipc(tmp_path):
    f = str(tmp_path / "state.json")
    live.write_json_atomic(f, {"status": "RUNNING", "n": 1})
    assert live.read_json(f) == {"status": "RUNNING", "n": 1}
    # Tolerant reader on corrupt/partial file
    with open(f, "w") as fh:
        fh.write('{"status": "PARTIAL')
    assert live.read_json(f, {"fallback": True}) == {"fallback": True}

    cf = str(tmp_path / "control.json")
    live.send_control("pause", fpath=cf)
    assert live.peek_control(fpath=cf)["action"] == "pause"
    assert live.consume_control(fpath=cf)["action"] == "pause"
    assert live.peek_control(fpath=cf) is None


def test_tail_events_handles_partial_and_corrupt_lines(tmp_path):
    root = str(tmp_path)
    p = live.worker_stream_path("w1", root=root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        fh.write(json.dumps({"ts": 1.0, "kind": "think", "text": "line1"}) + "\n")
        fh.write("{corrupt json\n")
        fh.write('{"ts": 2.0, "kind": "think", "text": "half')  # no trailing newline

    evs, off = live.tail_events("w1", offset=0, root=root)
    assert len(evs) == 1
    assert evs[0]["text"] == "line1"

    # Complete the partial line
    with open(p, "a") as fh:
        fh.write('-done"}\n')
    evs2, off2 = live.tail_events("w1", offset=off, root=root)
    assert len(evs2) == 1
    assert evs2[0]["text"] == "half-done"
    assert off2 > off


def _write_fake_claude(tmp_path, body):
    script = tmp_path / "fake_claude.py"
    script.write_text(f"#!{sys.executable}\n{body}\n")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return str(script)


def test_call_claude_streaming_large_stdin_and_rate_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "live_dir", lambda root=None: str(tmp_path / "live"))
    sys_file = tmp_path / "sys.txt"
    sys_file.write_text("system rules\n")
    lg = batch_driver.Ledger(str(tmp_path / "ledger.jsonl"))

    fake = _write_fake_claude(tmp_path, """
import json, sys
data = sys.stdin.read()
sys.stderr.write("diagnostic stderr\\n" * 500)
sys.stderr.flush()
events = [
    {"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": "thinking_delta", "thinking": "step 1\\nstep 2\\n"}}},
    {"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": '{"filename": "foo.c"}'}}},
    {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "unifiedWindows": {
        "five_hour": {"utilization": 0.37, "resetsAt": 1999999999, "status": "allowed"},
        "seven_day": {"utilization": 0.12, "resetsAt": 2000000000, "status": "allowed"},
    }}},
    {"type": "result", "is_error": False, "total_cost_usd": 0.042,
     "usage": {"input_tokens": 5, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 500, "output_tokens": 20},
     "structured_output": {"stdin_len": len(data), "ok": True}},
]
for e in events:
    print(json.dumps(e), flush=True)
""")
    big_prompt = "X" * 160_000  # > 64KB pipe buffer
    out, cost, usage = batch_driver.call_claude(
        big_prompt, {"type": "object"}, str(sys_file),
        ledger=lg, label="demo:draft_b0", worker_id="demo", claude_bin=fake,
    )
    assert out == {"stdin_len": 160_000, "ok": True}
    assert abs(cost - 0.042) < 1e-6
    assert usage["cache_read_input_tokens"] == 500
    assert live.load_rate_limits()["five_hour"]["used_percentage"] == 37.0
    evs, _ = live.tail_events("demo", offset=0)
    kinds = [e["kind"] for e in evs]
    assert "think" in kinds
    assert "out" in kinds


def test_call_claude_timeout_kills_process_tree(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "live_dir", lambda root=None: str(tmp_path / "live"))
    sys_file = tmp_path / "sys.txt"
    sys_file.write_text("sys\n")
    child_pid_file = tmp_path / "child.pid"
    fake = _write_fake_claude(tmp_path, f"""
import subprocess, sys, time
c = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
open({str(child_pid_file)!r}, "w").write(str(c.pid))
time.sleep(60)
""")
    with pytest.raises(batch_driver.DriverError, match="timed out"):
        batch_driver.call_claude(
            "hi", {"type": "object"}, str(sys_file),
            label="hang:test", worker_id="hang", timeout=1, claude_bin=fake,
        )
    if child_pid_file.exists():
        cpid = int(child_pid_file.read_text().strip())
        assert not live.pid_alive(cpid)


def test_call_claude_rate_limit_error_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "live_dir", lambda root=None: str(tmp_path / "live"))
    sys_file = tmp_path / "sys.txt"
    sys_file.write_text("sys\n")
    fake = _write_fake_claude(tmp_path, """
import json, sys
print(json.dumps({"type": "result", "is_error": True, "result": "You've hit your 5-hour limit"}), flush=True)
sys.exit(1)
""")
    with pytest.raises(batch_driver.RateLimitError):
        batch_driver.call_claude(
            "hi", {"type": "object"}, str(sys_file),
            label="rl:test", worker_id="rl", claude_bin=fake,
        )
