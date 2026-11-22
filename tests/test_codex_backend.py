"""Unit and fake-CLI integration tests for the Codex Plus backend (`wc1.codex`, `batch_driver`, `overnight`)."""
import datetime
import json
import os
import stat
import subprocess
import sys
import time

import pytest

from wc1 import batch_driver, codex, live, overnight, path


def _assert_openai_strict_schema(node, loc="$"):
    if isinstance(node, list):
        for i, item in enumerate(node):
            _assert_openai_strict_schema(item, f"{loc}[{i}]")
        return
    if not isinstance(node, dict):
        return
    for bad_kw in ("minItems", "maxItems", "uniqueItems", "minLength", "maxLength", "pattern", "minimum", "maximum"):
        assert bad_kw not in node, f"unsupported strict keyword {bad_kw} at {loc}"
    if node.get("type") == "object" or "properties" in node:
        assert node.get("additionalProperties") is False, f"missing additionalProperties:false at {loc}"
        props = node.get("properties") or {}
        req = set(node.get("required") or [])
        assert req == set(props.keys()), f"required mismatch at {loc}: {req} vs {set(props.keys())}"
        for k, v in props.items():
            _assert_openai_strict_schema(v, f"{loc}.{k}")
    if "items" in node:
        _assert_openai_strict_schema(node["items"], f"{loc}[]")


def test_strictify_schema_covers_all_driver_and_repair_schemas():
    schemas = [
        batch_driver.SEMANTIC_SCHEMA,
        batch_driver.BATCH_C_SCHEMA,
        batch_driver.REPAIR_C_SCHEMA,
        batch_driver.T4_AND_DOC_SCHEMA,
        batch_driver.T4_PATCH_SCHEMA,
        overnight.CODEX_VERIFY_PATCH_SCHEMA,
    ]
    for sc in schemas:
        strict = codex.strictify_schema(sc)
        _assert_openai_strict_schema(strict)
    # Original Claude schemas remain untouched (no mutation)
    assert "minItems" in batch_driver.SEMANTIC_SCHEMA["properties"]["functions"]["items"]["properties"]["evidence"]
    assert "header_additions" not in batch_driver.BATCH_C_SCHEMA["required"]
    assert "header_additions" in codex.strictify_schema(batch_driver.BATCH_C_SCHEMA)["required"]


def test_model_effort_validation_and_stage_matrix():
    # Default matrix is the Phase 3 Pareto-optimal winner (gpt-6.2-sol:low across all stages)
    dmat = codex.build_stage_matrix()
    for st in codex.STAGES:
        assert dmat[st] == ("gpt-6.2-sol", "low")

    m = codex.build_stage_matrix(
        default_model="gpt-6-luna",
        default_effort="low",
        overrides={"stage1": "gpt-6.2-sol:medium", "stage3": ":medium", "stage4": "gpt-6.1-terra"},
    )
    assert m["stage1"] == ("gpt-6.2-sol", "medium")
    assert m["stage2"] == ("gpt-6-luna", "low")
    assert m["stage3"] == ("gpt-6-luna", "medium")
    assert m["stage4"] == ("gpt-6.1-terra", "low")
    assert m["repair"] == ("gpt-6-luna", "low")

    # astra and xhigh/max/ultra are strictly rejected
    for bad_model in ("gpt-6.2-astra", "gpt-6-astra", "ASTRA"):
        with pytest.raises(ValueError, match="excluded"):
            codex.validate_model_effort(bad_model, "low")
    for bad_eff in ("xhigh", "max", "ultra"):
        with pytest.raises(ValueError, match="excluded"):
            codex.validate_model_effort("gpt-6.2-sol", bad_eff)


def test_parse_codex_json_line_and_error_classification():
    assert codex.parse_codex_json_line('{"type":"thread.started","thread_id":"t-123"}') == {
        "kind": "thread_started", "thread_id": "t-123",
    }
    ev_msg = codex.parse_codex_json_line(
        '{"type":"item.completed","item":{"id":"i1","type":"agent_message","text":"{\\"ok\\":true}"}}'
    )
    assert ev_msg["kind"] == "agent_message" and ev_msg["text"] == '{"ok":true}'
    ev_tool = codex.parse_codex_json_line(
        '{"type":"item.started","item":{"id":"i2","type":"command_execution","command":"ls"}}'
    )
    assert ev_tool["kind"] == "tool_violation" and ev_tool["tool_type"] == "command_execution"
    ev_done = codex.parse_codex_json_line(
        '{"type":"turn.completed","usage":{"input_tokens":1000,"cached_input_tokens":800,"output_tokens":50}}'
    )
    assert ev_done["kind"] == "turn_completed" and ev_done["usage"]["cached_input_tokens"] == 800

    # Strict rate-limit error classification: real limits YES, auth/CLI/network/schema NO
    assert codex.is_codex_rate_limit_error(1, "Error: usage_limit_reached, try again in 45 minutes")
    assert codex.is_codex_rate_limit_error(1, "HTTP status 429: Too Many Requests")
    assert codex.is_codex_rate_limit_error(1, "You've hit your usage limit for Codex")
    assert codex.is_codex_rate_limit_error(1, "request failed", rl_after={"rate_limit_reached_type": "primary"})
    assert not codex.is_codex_rate_limit_error(0, "usage_limit_reached")
    assert not codex.is_codex_rate_limit_error(1, "401 Unauthorized: not logged in")
    assert not codex.is_codex_rate_limit_error(1, "error: unrecognized argument --bogus")
    assert not codex.is_codex_rate_limit_error(1, "invalid_json_schema: minItems not supported")
    assert not codex.is_codex_rate_limit_error(1, "Connection refused (DNS lookup failed)")

    now = 1_800_000_000.0
    assert abs(codex.parse_codex_reset_text("try again in 1h 30m", now=now) - (now + 5400)) < 2
    assert codex.parse_codex_reset_text("resets_at=1800003600", now=now) == 1800003600.0
    assert codex.parse_codex_reset_text("usage limit reached with no timestamp", now=now) is None


def test_freshness_and_quota_gate_cold_start_and_caps():
    now = 1_800_000_000.0
    fresh_rl = {
        "observed_at": now - 120,
        "primary": {"used_percent": 50.0, "window_minutes": 300, "resets_at": now + 3600},
        "secondary": {"used_percent": 20.0, "window_minutes": 10080, "resets_at": now + 86400},
    }
    assert codex.is_window_fresh(fresh_rl["primary"], fresh_rl["observed_at"], now=now)[0] is True

    # Stale observed_at MUST fail freshness even though resets_at > now
    stale_rl = dict(fresh_rl, observed_at=now - 3600)
    ok_stale, msg_stale = codex.is_window_fresh(stale_rl["primary"], stale_rl["observed_at"], now=now, max_age_s=1800)
    assert not ok_stale and "stale" in msg_stale

    # Cold start / stale telemetry with window_budget < 1.0 -> error (no hidden calls!)
    g_cold = codex.check_codex_quota_gate({}, window_budget=0.8, now=now)
    assert g_cold["action"] == "error" and "fresh" in g_cold["reason"]
    g_stale = codex.check_codex_quota_gate(stale_rl, window_budget=0.8, now=now, max_age_s=1800)
    assert g_stale["action"] == "error" and "stale" in g_stale["reason"]

    # window_budget == 1.0 allows cold start without pre-emptive short-window threshold
    g_full = codex.check_codex_quota_gate({}, window_budget=1.0, now=now)
    assert g_full["action"] == "ok"

    # Fresh 85% >= 0.80 -> wait until resets_at + margin
    high_5h = dict(fresh_rl, primary={"used_percent": 85.0, "window_minutes": 300, "resets_at": now + 1200})
    g_wait = codex.check_codex_quota_gate(high_5h, window_budget=0.8, now=now)
    assert g_wait["action"] == "wait" and 1200 <= g_wait["wait_seconds"] <= 1300
    # Same 85% under window_budget=1.0 -> ok
    assert codex.check_codex_quota_gate(high_5h, window_budget=1.0, now=now)["action"] == "ok"

    # Mechanical 7d absolute cap & 7d delta cap & total calls cap -> stop_budget
    high_7d = dict(fresh_rl, secondary={"used_percent": 90.0, "window_minutes": 10080, "resets_at": now + 86400})
    assert codex.check_codex_quota_gate(high_7d, window_budget=1.0, now=now, max_7d_pct=90.0)["action"] == "stop_budget"
    delta_7d = dict(fresh_rl, secondary={"used_percent": 30.0, "window_minutes": 10080, "resets_at": now + 86400})
    assert codex.check_codex_quota_gate(
        delta_7d, window_budget=1.0, now=now, max_7d_delta_pp=25.0, start_7d_pct=5.0,
    )["action"] == "stop_budget"
    assert codex.check_codex_quota_gate(
        fresh_rl, window_budget=1.0, now=now, total_calls_used=10, max_total_calls=10,
    )["action"] == "stop_budget"


def test_provider_separation_in_live_and_ledger(tmp_path):
    root = str(tmp_path)
    live.save_rate_limits({"updated_at": 100.0, "five_hour": {"utilization": 0.4, "resets_at": 200.0}}, root=root)
    live.save_codex_rate_limits({
        "observed_at": 110.0, "plan_type": "plus",
        "primary": {"used_percent": 15.0, "window_minutes": 300, "resets_at": 500.0},
    }, root=root)
    assert live.load_rate_limits(root=root)["five_hour"]["utilization"] == 0.4
    assert "primary" not in live.load_rate_limits(root=root)
    assert live.load_codex_rate_limits(root=root)["primary"]["used_percent"] == 15.0
    assert "five_hour" not in live.load_codex_rate_limits(root=root)

    # Mixed ledger keeps Claude USD completely separate from Codex calls/tokens
    now = 1_700_000_000.0
    iso = datetime.datetime.fromtimestamp(now - 60, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ldir = tmp_path / "ledgers"
    lg = batch_driver.Ledger(str(ldir / "mixed.jsonl"))
    lg.record("claude_call", label="c1", cost_usd=0.25, usage={"input_tokens": 100, "output_tokens": 50})
    lg.record("codex_call", provider="codex", label="x1", model="gpt-6-luna", effort="low",
              usage={"input_tokens": 2000, "cached_input_tokens": 1500, "output_tokens": 200, "reasoning_output_tokens": 80},
              telemetry_observed=True, primary_delta_pp=0.5, secondary_delta_pp=0.1, estimated_primary_pp=0.4)
    s = lg.summary()
    assert s["claude_calls"] == 1 and s["codex_calls"] == 1 and s["calls"] == 2
    assert abs(s["cost_usd"] - 0.25) < 1e-6
    assert s["codex_cache_hit_pct"] == 75.0
    assert s["codex_reasoning_tokens"] == 80
    assert s["codex_primary_delta_pp"] == 0.5
    # Rewrite timestamps for rolling_window_spend check
    rows = [dict(e, ts=iso) for e in lg.entries]
    (ldir / "mixed.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    spend, c_calls, _ = overnight.rolling_window_spend(str(ldir), now=now)
    assert abs(spend - 0.25) < 1e-6 and c_calls == 1


def _make_fake_codex(tmp_path, script_body):
    p = tmp_path / "fake_codex"
    p.write_text("#!/usr/bin/env python3\n" + script_body)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def test_call_codex_fake_cli_success_rollout_telemetry_and_isolation(tmp_path):
    codex_home = tmp_path / "codex_home"
    now = time.time()
    day = datetime.datetime.now()
    sess_dir = codex_home / "sessions" / f"{day.year:04d}" / f"{day.month:02d}" / f"{day.day:02d}"
    sess_dir.mkdir(parents=True)
    # Seed initial telemetry snapshot (10% 5h, 2% 7d)
    (sess_dir / "rollout-seed.jsonl").write_text(json.dumps({
        "timestamp": datetime.datetime.fromtimestamp(now - 30, tz=datetime.timezone.utc).isoformat(),
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "rate_limits": {
                "plan_type": "plus",
                "primary": {"used_percent": 10.0, "window_minutes": 300, "resets_at": int(now + 3600)},
                "secondary": {"used_percent": 2.0, "window_minutes": 10080, "resets_at": int(now + 86400)},
            },
        },
    }) + "\n")

    argv_dump = tmp_path / "argv.json"
    fake_cli = _make_fake_codex(tmp_path, f"""
import datetime, json, os, sys, time
argv = sys.argv[1:]
open({str(argv_dump)!r}, "w").write(json.dumps(argv))
prompt = sys.stdin.read()
assert "HELLO_PROMPT" in prompt
# Write a rollout file for thread-abc with updated rate_limits (11.5% 5h, 2.5% 7d) and reasoning tokens
rpath = os.path.join({str(sess_dir)!r}, "rollout-2026-thread-abc.jsonl")
now_ts = time.time()
with open(rpath, "w") as fh:
    fh.write(json.dumps({{
        "timestamp": datetime.datetime.fromtimestamp(now_ts, tz=datetime.timezone.utc).isoformat(),
        "type": "event_msg",
        "payload": {{
            "type": "token_count",
            "info": {{"total_token_usage": {{"input_tokens": 5000, "cached_input_tokens": 4000, "output_tokens": 300, "reasoning_output_tokens": 120}}}},
            "rate_limits": {{
                "plan_type": "plus",
                "primary": {{"used_percent": 11.5, "window_minutes": 300, "resets_at": {int(now + 3600)}}},
                "secondary": {{"used_percent": 2.5, "window_minutes": 10080, "resets_at": {int(now + 86400)}}},
            }},
        }},
    }}) + "\\n")
print(json.dumps({{"type": "thread.started", "thread_id": "thread-abc"}}), flush=True)
print(json.dumps({{"type": "item.completed", "item": {{"id": "1", "type": "agent_message", "text": json.dumps({{"answer": "ok"}})}}}}), flush=True)
print(json.dumps({{"type": "turn.completed", "usage": {{"input_tokens": 5000, "cached_input_tokens": 4000, "output_tokens": 300}}}}), flush=True)
""")

    sys_f = tmp_path / "sys.txt"
    sys_f.write_text("BASE RULES\n")
    lg = batch_driver.Ledger(str(tmp_path / "lg.jsonl"))
    out, meta = codex.call_codex(
        "HELLO_PROMPT",
        {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]},
        str(sys_f),
        model="gpt-6-luna",
        effort="low",
        ledger=lg,
        label="demo:stage1",
        codex_bin=fake_cli,
        codex_home=str(codex_home),
        root=str(tmp_path),
    )
    assert out == {"answer": "ok"}
    assert meta["telemetry_observed"] is True
    assert meta["usage"]["cached_input_tokens"] == 4000
    assert meta["usage"]["reasoning_output_tokens"] == 120
    assert meta["usage"]["cache_hit_pct"] == 80.0
    assert meta["primary_delta_pp"] == 1.5
    assert meta["secondary_delta_pp"] == 0.5
    argv = json.loads(argv_dump.read_text())
    assert "--ignore-user-config" in argv and "--ignore-rules" in argv
    assert "-s" in argv and "read-only" in argv
    assert "project_doc_max_bytes=0" in argv and "include_environment_context=false" in argv
    assert live.load_codex_rate_limits(root=str(tmp_path))["primary"]["used_percent"] == 11.5


def test_call_codex_fake_cli_timeout_tool_violation_and_per_call_quota_block(tmp_path):
    sys_f = tmp_path / "sys.txt"
    sys_f.write_text("RULES\n")

    # 1. Timeout kills process tree (including child) and records codex_timeout
    gpid = tmp_path / "g.pid"
    slow_cli = _make_fake_codex(tmp_path, f"""
import subprocess, sys, time
p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
open({str(gpid)!r}, "w").write(str(p.pid))
time.sleep(60)
""")
    lg = batch_driver.Ledger(str(tmp_path / "to.jsonl"))
    with pytest.raises(TimeoutError):
        codex.call_codex(
            "hi", {"type": "object", "properties": {}}, str(sys_f),
            ledger=lg, label="to", timeout=1.0, codex_bin=slow_cli,
            codex_home=str(tmp_path / "empty_home"), root=str(tmp_path),
        )
    assert lg.entries[-1]["stage"] == "codex_timeout"
    if gpid.exists():
        pid = int(gpid.read_text())
        deadline = time.time() + 3.0
        while live.pid_alive(pid) and time.time() < deadline:
            time.sleep(0.05)
        assert not live.pid_alive(pid)

    # 2. Forbidden tool execution during stateless call is rejected
    tool_cli = _make_fake_codex(tmp_path, """
import json
print(json.dumps({"type": "item.started", "item": {"id": "1", "type": "command_execution", "command": "rm -rf /"}}))
print(json.dumps({"type": "item.completed", "item": {"id": "2", "type": "agent_message", "text": "{}"}}))
""")
    with pytest.raises(RuntimeError, match="forbidden tool"):
        codex.call_codex(
            "hi", {"type": "object", "properties": {}}, str(sys_f),
            codex_bin=tool_cli, codex_home=str(tmp_path / "empty_home"), root=str(tmp_path),
        )

    # 3. Mechanical per-call quota gate blocks BEFORE ever spawning the CLI
    marker = tmp_path / "should_not_exist"
    guard_cli = _make_fake_codex(tmp_path, f"open({str(marker)!r}, 'w').write('ran')\n")
    now = time.time()
    live.save_codex_rate_limits({
        "observed_at": now - 10,
        "primary": {"used_percent": 50.0, "window_minutes": 300, "resets_at": now + 3600},
        "secondary": {"used_percent": 31.0, "window_minutes": 10080, "resets_at": now + 86400},
    }, root=str(tmp_path))
    with pytest.raises(codex.CodexQuotaError) as ei:
        codex.call_codex(
            "hi", {"type": "object", "properties": {}}, str(sys_f),
            codex_bin=guard_cli, codex_home=str(tmp_path / "empty_home"), root=str(tmp_path),
            quota_guard={"window_budget": 1.0, "max_7d_delta_pp": 25.0, "start_7d_pct": 5.0},
        )
    assert ei.value.action == "stop_budget"
    assert not marker.exists()


def test_codex_structured_verify_patch_security_and_anti_weakening(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "Makefile").write_text("all:\n\techo ok\n")
    (repo / "src" / "demo").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "analysis" / "symbols").mkdir(parents=True)
    subprocess.run(["git", "add", "Makefile"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)

    c_file = repo / "src" / "demo" / "foo_reference.c"
    c_file.write_text("int Foo(int x) { return x / 2; }\n")
    t_file = repo / "tests" / "test_demo.py"
    orig_test = (
        "from wc1 import t4spec\nfrom wc1.t4spec import T4Case\n"
        "def test_foo():\n"
        "    cases = [T4Case(args=(-3,), label='neg')]\n"
        "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, cases, out_regs=('eax',))\n"
    )
    t_file.write_text(orig_test)
    toml_file = repo / "analysis" / "symbols" / "demo.toml"
    toml_file.write_text('[[func]]\naddr = 0x1000\nname = "Foo"\nref = "src/demo/foo_reference.c"\n')

    item = {"area": "demo", "src_subdir": "demo", "header": None}
    bad_res = {
        "diagnosis": "trying sneaky patches",
        "file_patches": [
            {"path": "Makefile", "old": "echo ok", "new": "echo hacked"},
            {"path": "../outside.txt", "old": "a", "new": "b"},
            {"path": "analysis/symbols/demo.toml", "old": 'ref = "src/demo/foo_reference.c"',
             "new": 'ref = "src/demo/foo_reference.c"\nref_verified_by = "difftest: tests/test_demo.py::test_foo"'},
            {"path": "tests/test_demo.py", "old": "args=(-3,)", "new": "args=(-4,)"},
            {"path": "src/demo/foo_reference.c", "old": "x / 2", "new": "x >> ???"},
        ],
    }
    pres = overnight._apply_codex_verify_patches(
        item, (), bad_res, cwd=str(repo),
        compile_check_fn=lambda files: [(files[0], "syntax error")],
    )
    assert pres["applied"] == 0
    assert len(pres["rejected"]) == 5
    assert (repo / "Makefile").read_text() == "all:\n\techo ok\n"
    assert t_file.read_text() == orig_test
    assert c_file.read_text() == "int Foo(int x) { return x / 2; }\n"
    assert "ref_verified_by" not in toml_file.read_text()

    # Valid C fix is accepted and applied
    good_res = {
        "diagnosis": "0x1004 uses sar eax, 1",
        "file_patches": [{"path": "src/demo/foo_reference.c", "old": "x / 2", "new": "x >> 1"}],
    }
    pres2 = overnight._apply_codex_verify_patches(
        item, (), good_res, cwd=str(repo), compile_check_fn=lambda files: [],
    )
    assert pres2["applied"] == 1 and not pres2["rejected"]
    assert "x >> 1" in c_file.read_text()


def test_overnight_codex_e2e_rate_limit_resume_no_sleep_unknown_reset_and_cold_start(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("orig\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)

    empty_codex_home = tmp_path / "empty_codex_home"
    empty_codex_home.mkdir()
    monkeypatch.setattr(overnight, "path", lambda *parts: os.path.join(str(repo), *parts))
    monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(repo), "build", "live"))
    monkeypatch.setattr(overnight, "_reset_wine", lambda: None)

    item_a = {
        "key": ("full", "MOD_A", (0x1000,)), "mode": "full", "module": "MOD_A", "area": "mod_a",
        "src_subdir": "mod_a", "header": None, "limit": None, "count": 1, "addrs": [0x1000],
        "module_total": 1, "total_insns": 20, "avg_insns": 20.0,
    }
    prog = {"done": 794}
    monkeypatch.setattr(overnight, "progress_done_count", lambda: (prog["done"], 1010, 414, prog["done"] - 414))

    # Case 1: Cold start with window_budget=0.8 and no fresh telemetry -> rc=2, zero calls
    spawned = []
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [item_a])
    monkeypatch.setattr(overnight, "_run_subprocess_logged", lambda *a, **kw: spawned.append(a[0]) or (0, ""))
    rc_cold = overnight.run_overnight(
        provider="codex", window_budget=0.8, codex_home=str(empty_codex_home), codex_repair_calls=0,
    )
    assert rc_cold == 2 and spawned == []

    # Case 2: Rate limit with known resets_at -> sleep -> resume same chunk -> commit cleanly
    sleeps = []
    monkeypatch.setattr(overnight, "_sleep_with_heartbeat", lambda secs, reason, *a, **kw: sleeps.append((secs, reason)))
    runs = {"n": 0}
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [item_a] if runs["n"] == 0 else [])

    def subproc_rl_resume(cmd, log_fh, **kw):
        if cmd[0] == sys.executable:
            runs["n"] += 1
            if runs["n"] == 1:
                (repo / "src" / "mod_a").mkdir(parents=True, exist_ok=True)
                (repo / "src" / "mod_a" / "f.c").write_text("int f(void){return 1;}\n")
                res_ts = int(time.time() + 180)
                return batch_driver.EXIT_RATE_LIMIT, f"[RATE_LIMIT] usage_limit_reached resets_at={res_ts}\n"
            prog["done"] = 795
            batch_driver.Ledger(os.path.join(str(repo), "build", "ledger", "mod_a.jsonl")).record(
                "codex_call", provider="codex", model="gpt-6-luna", effort="low", usage={"input_tokens": 100},
            )
            return 0, "resumed ok\n"
        return 0, "IDENTICAL\n100 passed\n"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", subproc_rl_resume)
    rc_res = overnight.run_overnight(
        provider="codex", window_budget=1.0, sleep_on_limit=True,
        codex_home=str(empty_codex_home), codex_repair_calls=0,
    )
    assert rc_res == 0
    assert runs["n"] == 2 and len(sleeps) == 1 and sleeps[0][0] >= 180
    assert (repo / "src" / "mod_a" / "f.c").exists()
    st = live.read_json(live.state_path())
    assert st["commits"][-1]["provider"] == "codex"
    assert "USD" not in st["commits"][-1]["message"]

    # Case 3: Rate limit with --no-sleep -> clean rollback & exit 0
    item_b = dict(item_a, key=("full", "MOD_B", (0x2000,)), module="MOD_B", area="mod_b", src_subdir="mod_b")
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [item_b])

    def subproc_rl_nosleep(cmd, log_fh, **kw):
        (repo / "tracked.txt").write_text("dirty\n")
        (repo / "temp_b.c").write_text("int b;\n")
        return batch_driver.EXIT_RATE_LIMIT, f"[RATE_LIMIT] usage_limit_reached resets_at={int(time.time() + 300)}\n"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", subproc_rl_nosleep)
    rc_ns = overnight.run_overnight(
        provider="codex", window_budget=1.0, sleep_on_limit=False,
        codex_home=str(empty_codex_home), codex_repair_calls=0,
    )
    assert rc_ns == 0
    assert (repo / "tracked.txt").read_text() == "orig\n"
    assert not (repo / "temp_b.c").exists()

    # Case 4: Rate limit with UNKNOWN resets_at -> stops immediately with EXIT_RATE_LIMIT & clean rollback
    sleeps.clear()
    def subproc_rl_unknown(cmd, log_fh, **kw):
        (repo / "tracked.txt").write_text("dirty2\n")
        (repo / "temp_u.c").write_text("int u;\n")
        return batch_driver.EXIT_RATE_LIMIT, "[RATE_LIMIT] usage_limit_reached\n"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", subproc_rl_unknown)
    rc_unk = overnight.run_overnight(
        provider="codex", window_budget=1.0, sleep_on_limit=True,
        codex_home=str(empty_codex_home), codex_repair_calls=0,
    )
    assert rc_unk == batch_driver.EXIT_RATE_LIMIT
    assert sleeps == []
    assert (repo / "tracked.txt").read_text() == "orig\n"
    assert not (repo / "temp_u.c").exists()


def test_overnight_codex_dry_run_and_tui_rejection():
    with pytest.raises(SystemExit):
        overnight.main(["--provider", "codex", "--tui"])
    if not os.path.exists(path("original", "install", "war.exe")):
        pytest.skip("needs original/install/war.exe")
    rc = overnight.main(["--provider", "codex", "--dry-run", "--window-budget", "1.0", "--max-modules", "3"])
    assert rc == 0


def test_overnight_early_stop_skips_verify_and_repair(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("orig\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    empty_home = tmp_path / "empty_home"
    empty_home.mkdir()
    monkeypatch.setattr(overnight, "path", lambda *parts: os.path.join(str(repo), *parts))
    monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(repo), "build", "live"))
    monkeypatch.setattr(overnight, "_reset_wine", lambda: None)
    monkeypatch.setattr(overnight, "progress_done_count", lambda: (794, 1010, 414, 380))

    item_a = {
        "key": ("full", "MOD_A", (0x1000,)), "mode": "full", "module": "MOD_A", "area": "mod_a",
        "src_subdir": "mod_a", "header": None, "limit": None, "count": 1, "addrs": [0x1000],
        "module_total": 1, "total_insns": 20, "avg_insns": 20.0,
    }
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [item_a])
    verify_called = []

    def subproc_es(cmd, log_fh, **kw):
        if cmd[:2] == ["make", "verify"]:
            verify_called.append(True)
            return 0, ""
        (repo / "analysis" / "symbols").mkdir(parents=True, exist_ok=True)
        (repo / "analysis" / "symbols" / "mod_a.toml").write_text("bad\n")
        return 1, "[DRIVER ERROR] symbols errors after semantic pass\n"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", subproc_es)
    rc = overnight.run_overnight(
        provider="codex", window_budget=1.0, max_modules=1,
        codex_home=str(empty_home), codex_repair_calls=1,
    )
    assert rc == 0
    assert verify_called == []
    assert not (repo / "analysis" / "symbols" / "mod_a.toml").exists()


def test_call_llm_codex_strips_base_total_calls_without_max_total_calls(tmp_path):
    """Regression: `_build_codex_runtime` sets `_base_total_calls` even when `--codex-max-total-calls`
    is None; `_call_llm` must always strip it before calling `codex.call_codex`."""
    import argparse
    ap = argparse.ArgumentParser()
    batch_driver._add_provider_args(ap)
    args = ap.parse_args(["--provider", "codex", "--codex-window-budget", "1.0"])
    matrix, guard = batch_driver._build_codex_runtime(args)
    assert "_base_total_calls" in guard and guard["max_total_calls"] is None

    fake_cli = _make_fake_codex(tmp_path, """
import json
print(json.dumps({"type": "thread.started", "thread_id": "t-ok"}), flush=True)
print(json.dumps({"type": "item.completed", "item": {"id": "1", "type": "agent_message", "text": json.dumps({"ok": True})}}), flush=True)
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 0, "output_tokens": 10}}), flush=True)
""")
    sys_f = tmp_path / "sys.txt"
    sys_f.write_text("RULES\n")
    lg = batch_driver.Ledger(str(tmp_path / "lg.jsonl"))
    out, cost, usage = batch_driver._call_llm(
        "hi",
        {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]},
        str(sys_f),
        provider="codex",
        stage="stage1",
        codex_matrix=matrix,
        codex_bin=fake_cli,
        codex_home=str(tmp_path / "empty_home"),
        codex_quota_guard=guard,
        ledger=lg,
        label="reg:stage1",
    )
    assert out == {"ok": True} and cost == 0.0 and usage["input_tokens"] == 100


# ---- Review follow-up tests (M1-M4, S1-S16, N2) ------------------------------

def _git_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("orig\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def _item(name="MOD_A", area="mod_a", addr=0x1000, header=None):
    return {
        "key": ("full", name, (addr,)), "mode": "full", "module": name, "area": area,
        "src_subdir": area, "header": header, "limit": None, "count": 1, "addrs": [addr],
        "module_total": 1, "total_insns": 20, "avg_insns": 20.0,
    }


def test_gate_after_reset_resume_only_after_confirmed_reset():
    """M1: below 1.0, expired telemetry passes only right after a confirmed reset sleep."""
    slept = 2_000_000_000.0
    now = slept + 60
    rl = {
        "observed_at": slept - 600,
        "primary": {"used_percent": 100.0, "window_minutes": 300, "resets_at": slept},
        "secondary": {"used_percent": 30.0, "window_minutes": 10080, "resets_at": now + 86400},
    }
    ok = codex.check_codex_quota_gate(rl, window_budget=0.8, now=now, after_reset=True, slept_resets_at=slept)
    assert ok["action"] == "ok" and ok.get("after_reset") is True
    # Cold start (no after_reset) still errors with expired telemetry.
    assert codex.check_codex_quota_gate(rl, window_budget=0.8, now=now)["action"] == "error"
    # Not yet past the slept-through reset: the window is still live and exhausted.
    early = codex.check_codex_quota_gate(
        rl, window_budget=0.8, now=slept - 30, after_reset=True, slept_resets_at=slept,
    )
    assert early["action"] == "wait" and not early.get("after_reset")
    # Telemetry describes a later window than the one slept through.
    rl_later = dict(rl, primary=dict(rl["primary"], resets_at=slept + 1000))
    assert codex.check_codex_quota_gate(
        rl_later, window_budget=0.8, now=slept + 2000, after_reset=True, slept_resets_at=slept,
    )["action"] == "error"
    # after_reset without a slept timestamp, and with empty telemetry.
    assert codex.check_codex_quota_gate(
        rl, window_budget=0.8, now=now, after_reset=True, slept_resets_at=None,
    )["action"] == "error"
    assert codex.check_codex_quota_gate(
        {}, window_budget=0.8, now=now, after_reset=True, slept_resets_at=slept,
    )["action"] == "error"
    # overnight helper: only once now >= slept.
    assert overnight._after_reset_kwargs(None) == {}
    assert overnight._after_reset_kwargs(slept, now=slept - 1) == {}
    assert overnight._after_reset_kwargs(slept, now=slept + 1) == {"after_reset": True, "slept_resets_at": slept}


def test_overnight_codex_budget_below_one_resumes_after_reset_sleep(tmp_path, monkeypatch):
    """M1 e2e: at --window-budget 0.8 a rate-limited chunk sleeps, then resumes with
    --codex-after-reset-ts and commits; a cold start on the expired telemetry still errors."""
    repo = _git_repo(tmp_path)
    empty_home = tmp_path / "empty_home"
    empty_home.mkdir()
    monkeypatch.setattr(overnight, "path", lambda *parts: os.path.join(str(repo), *parts))
    monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(repo), "build", "live"))
    monkeypatch.setattr(overnight, "_reset_wine", lambda: None)
    real_time = time.time
    off = {"s": 0.0}
    monkeypatch.setattr(time, "time", lambda: real_time() + off["s"])
    prog = {"done": 794}
    monkeypatch.setattr(overnight, "progress_done_count", lambda: (prog["done"], 1010, 414, prog["done"] - 414))

    now = time.time()
    live.save_codex_rate_limits({
        "observed_at": now - 10, "source": "test",
        "primary": {"used_percent": 10.0, "window_minutes": 300, "resets_at": now + 3600},
        "secondary": {"used_percent": 30.0, "window_minutes": 10080, "resets_at": now + 86400},
    })
    sleeps = []

    def fake_sleep(secs, reason, *a, **kw):
        sleeps.append(secs)
        off["s"] += secs

    monkeypatch.setattr(overnight, "_sleep_with_heartbeat", fake_sleep)
    runs = {"n": 0}
    child_cmds = []
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [_item()] if runs["n"] < 2 else [])

    def subproc(cmd, log_fh, **kw):
        if cmd[0] != sys.executable:
            return 0, "IDENTICAL\n100 passed\n"
        runs["n"] += 1
        child_cmds.append(list(cmd))
        if runs["n"] == 1:
            (repo / "src" / "mod_a").mkdir(parents=True, exist_ok=True)
            (repo / "src" / "mod_a" / "f.c").write_text("int f(void){return 1;}\n")
            t = time.time()
            res_ts = int(t) + 180
            live.save_codex_rate_limits({
                "observed_at": t, "source": "test", "rate_limit_reached_type": "primary",
                "primary": {"used_percent": 100.0, "window_minutes": 300, "resets_at": res_ts},
                "secondary": {"used_percent": 35.0, "window_minutes": 10080, "resets_at": now + 86400},
            })
            return batch_driver.EXIT_RATE_LIMIT, f"[RATE_LIMIT] usage_limit_reached resets_at={res_ts}\n"
        prog["done"] = 795
        batch_driver.Ledger(os.path.join(str(repo), "build", "ledger", "mod_a.jsonl")).record(
            "codex_call", provider="codex", model="gpt-6-luna", effort="low", usage={"input_tokens": 100},
        )
        return 0, "resumed ok\n"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", subproc)
    rc = overnight.run_overnight(
        provider="codex", window_budget=0.8, sleep_on_limit=True,
        codex_home=str(empty_home), codex_repair_calls=0,
    )
    assert rc == 0
    assert runs["n"] == 2 and len(sleeps) == 1
    assert "--codex-after-reset-ts" not in child_cmds[0]
    assert "--codex-after-reset-ts" in child_cmds[1]
    st = live.read_json(live.state_path())
    assert st["commits"][-1]["provider"] == "codex"

    # Cold start on the same (now expired) telemetry: no after-reset pass, rc=2, no spawn.
    spawned = []
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [_item("MOD_B", "mod_b", 0x2000)])
    monkeypatch.setattr(overnight, "_run_subprocess_logged", lambda *a, **kw: spawned.append(a[0]) or (0, ""))
    rc_cold = overnight.run_overnight(
        provider="codex", window_budget=0.8, codex_home=str(empty_home), codex_repair_calls=0,
    )
    assert rc_cold == 2 and spawned == []


def test_call_llm_after_reset_pass_is_one_shot(tmp_path, monkeypatch):
    """M1: the child's after-reset pass covers exactly one call; the next one needs fresh telemetry."""
    monkeypatch.setattr(live, "live_dir", lambda root=None: str(tmp_path / "live"))
    now = time.time()
    live.save_codex_rate_limits({
        "observed_at": now - 4000, "source": "test",
        "primary": {"used_percent": 100.0, "window_minutes": 300, "resets_at": now - 100},
        "secondary": {"used_percent": 30.0, "window_minutes": 10080, "resets_at": now + 86400},
    })
    fake_cli = _make_fake_codex(tmp_path, """
import json
print(json.dumps({"type": "thread.started", "thread_id": "t-ok"}), flush=True)
print(json.dumps({"type": "item.completed", "item": {"id": "1", "type": "agent_message", "text": json.dumps({"ok": True})}}), flush=True)
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 0, "output_tokens": 10}}), flush=True)
""")
    sys_f = tmp_path / "sys.txt"
    sys_f.write_text("RULES\n")
    guard = {"window_budget": 0.8, "after_reset": True, "slept_resets_at": now - 100}
    kw = dict(
        provider="codex", stage="stage1", codex_bin=fake_cli,
        codex_home=str(tmp_path / "empty_home"), codex_quota_guard=guard,
        ledger=batch_driver.Ledger(str(tmp_path / "lg.jsonl")), label="m1:stage1",
    )
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}
    out, _cost, _usage = batch_driver._call_llm("hi", schema, str(sys_f), **kw)
    assert out == {"ok": True}
    assert guard["after_reset"] is False
    with pytest.raises(batch_driver.DriverError):
        batch_driver._call_llm("hi", schema, str(sys_f), **kw)


def test_save_codex_rate_limits_newer_snapshot_replaces_windows(tmp_path):
    """M2: a newer snapshot clears rate_limit_reached_type and drops absent windows;
    an older one is ignored."""
    f = str(tmp_path / "rl.json")
    now = time.time()
    live.save_codex_rate_limits({
        "observed_at": now - 100, "source": "a", "rate_limit_reached_type": "primary", "plan_type": "plus",
        "primary": {"used_percent": 100.0, "window_minutes": 300, "resets_at": now + 600},
        "secondary": {"used_percent": 40.0, "window_minutes": 10080, "resets_at": now + 86400},
    }, fpath=f)
    live.save_codex_rate_limits({
        "observed_at": now, "source": "b",
        "primary": {"used_percent": 5.0, "window_minutes": 300, "resets_at": now + 18000},
    }, fpath=f)
    got = live.load_codex_rate_limits(fpath=f)
    assert not got.get("rate_limit_reached_type")
    assert got["primary"]["used_percent"] == 5.0
    assert not got.get("secondary")
    assert got.get("plan_type") == "plus"
    # Older snapshot does not overwrite.
    live.save_codex_rate_limits({
        "observed_at": now - 500, "source": "old",
        "primary": {"used_percent": 99.0, "window_minutes": 300, "resets_at": now + 100},
    }, fpath=f)
    assert live.load_codex_rate_limits(fpath=f)["primary"]["used_percent"] == 5.0


def test_overnight_claude_nonzero_rc_toml_only_still_verifies(tmp_path, monkeypatch):
    """M3: the 'rc != 0 and no C files' early stop is Codex-only; Claude still verifies + repairs."""
    repo = _git_repo(tmp_path)
    monkeypatch.setattr(overnight, "path", lambda *parts: os.path.join(str(repo), *parts))
    monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(repo), "build", "live"))
    monkeypatch.setattr(overnight, "_reset_wine", lambda: None)
    monkeypatch.setattr(overnight, "progress_done_count", lambda: (794, 1010, 414, 380))
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [_item()])
    monkeypatch.setattr(overnight, "run_bounded_repair", lambda *a, **kw: (0, 0, False, ""))
    verify_called = []

    def subproc(cmd, log_fh, **kw):
        if cmd[:2] == ["make", "verify"]:
            verify_called.append(True)
            return 0, "IDENTICAL\n100 passed\n"
        (repo / "analysis" / "symbols").mkdir(parents=True, exist_ok=True)
        (repo / "analysis" / "symbols" / "mod_a.toml").write_text("# names\n")
        return 1, "[DRIVER ERROR] partial semantic pass\n"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", subproc)
    overnight.run_overnight(provider="claude", window_budget=1.0, max_modules=1)
    assert verify_called


def _patch_repo(tmp_path):
    repo = tmp_path / "prepo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "Makefile").write_text("all:\n\techo ok\n")
    for d in ("src/demo", "src/include", "tests", "analysis/symbols"):
        (repo / d).mkdir(parents=True)
    subprocess.run(["git", "add", "Makefile"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def test_codex_verify_patches_are_atomic_on_bad_toml(tmp_path):
    """M4: one invalid patch (TOML parse error) rejects the whole set; the valid C patch is not applied."""
    repo = _patch_repo(tmp_path)
    c_file = repo / "src" / "demo" / "foo.c"
    c_file.write_text("int Foo(int x) { return x / 2; }\n")
    toml_file = repo / "analysis" / "symbols" / "demo.toml"
    toml_src = '[[func]]\naddr = 0x1000\nname = "Foo"\n'
    toml_file.write_text(toml_src)
    res = {
        "diagnosis": "mixed",
        "file_patches": [
            {"path": "src/demo/foo.c", "old": "x / 2", "new": "x >> 1"},
            {"path": "analysis/symbols/demo.toml", "old": 'name = "Foo"', "new": "name = = "},
        ],
    }
    pres = overnight._apply_codex_verify_patches(
        {"area": "demo", "src_subdir": "demo", "header": None}, (), res,
        cwd=str(repo), compile_check_fn=lambda files: [],
    )
    assert pres["applied"] == 0 and pres["rejected"]
    assert c_file.read_text() == "int Foo(int x) { return x / 2; }\n"
    assert toml_file.read_text() == toml_src


def test_codex_verify_header_patch_compile_checks_dependents_and_restores(tmp_path):
    """M4: a header patch compile-checks every .c in src/<src_subdir>/; a failure restores all files."""
    repo = _patch_repo(tmp_path)
    hdr = repo / "src" / "include" / "demo.h"
    hdr.write_text("int Foo(int x);\n")
    a_c = repo / "src" / "demo" / "a.c"
    a_c.write_text('#include "demo.h"\nint Foo(int x) { return x / 2; }\n')
    b_c = repo / "src" / "demo" / "b.c"
    b_c.write_text('#include "demo.h"\nint Bar(void) { return Foo(4); }\n')
    checked = []

    def cc(files):
        checked.extend(files)
        return [(files[-1], "error: conflicting types")]

    res = {
        "diagnosis": "change prototype",
        "file_patches": [
            {"path": "src/include/demo.h", "old": "int Foo(int x);", "new": "short Foo(int x);"},
            {"path": "src/demo/a.c", "old": "int Foo(int x)", "new": "short Foo(int x)"},
        ],
    }
    pres = overnight._apply_codex_verify_patches(
        {"area": "demo", "src_subdir": "demo", "header": "src/include/demo.h"}, (), res,
        cwd=str(repo), compile_check_fn=cc,
    )
    assert pres["applied"] == 0
    assert {os.path.realpath(p) for p in checked} >= {os.path.realpath(str(a_c)), os.path.realpath(str(b_c))}
    assert hdr.read_text() == "int Foo(int x);\n"
    assert a_c.read_text() == '#include "demo.h"\nint Foo(int x) { return x / 2; }\n'
    assert b_c.read_text() == '#include "demo.h"\nint Bar(void) { return Foo(4); }\n'


def test_rate_limit_classifier_prefers_telemetry():
    """S1: confirmed rate_limit_reached_type beats incidental non-rate-limit words."""
    txt = "HTTP 429: authentication failed while retrying"
    assert codex.is_codex_rate_limit_error(1, txt, rl_after={"rate_limit_reached_type": "primary"})
    assert not codex.is_codex_rate_limit_error(1, txt)
    assert not codex.is_codex_rate_limit_error(0, txt, rl_after={"rate_limit_reached_type": "primary"})


def test_parse_codex_reset_text_relative_forms():
    """S2: relative reset durations."""
    now = 2_000_000_000.0
    assert codex.parse_codex_reset_text("please try again in 45 minutes", now=now) == now + 2700
    assert codex.parse_codex_reset_text("limit resets in 2 hours", now=now) == now + 7200
    assert codex.parse_codex_reset_text("try again in 1h 23m", now=now) == now + 4980
    assert codex.parse_codex_reset_text("retry in 90 seconds", now=now) == now + 90
    assert codex.parse_codex_reset_text("usage limit reached", now=now) is None


def test_parse_codex_json_line_item_type_allowlist():
    """S12: only reasoning/agent_message items pass; anything else is a tool violation."""
    def ev(itype, et="item.started"):
        item = {"id": "1"}
        if itype is not None:
            item["type"] = itype
        return json.dumps({"type": et, "item": item})

    for t in ("web_search", "future_tool", "command_execution", "mcp_tool_call"):
        r = codex.parse_codex_json_line(ev(t))
        assert r["kind"] == "tool_violation" and r["tool_type"] == t
    assert codex.parse_codex_json_line(ev(None, "item.updated"))["tool_type"] == "<untyped>"
    assert codex.parse_codex_json_line(ev("reasoning", "item.completed"))["kind"] == "reasoning"
    assert codex.parse_codex_json_line(ev("agent_message", "item.completed"))["kind"] == "agent_message"


def test_call_codex_kills_process_on_first_tool_violation(tmp_path):
    """S12: the process tree is terminated on the first violation, not at exit."""
    fake_cli = _make_fake_codex(tmp_path, """
import json, time
print(json.dumps({"type": "thread.started", "thread_id": "t-v"}), flush=True)
print(json.dumps({"type": "item.started", "item": {"id": "1", "type": "command_execution", "command": "ls"}}), flush=True)
time.sleep(30)
""")
    sys_f = tmp_path / "sys.txt"
    sys_f.write_text("RULES\n")
    t0 = time.monotonic()
    with pytest.raises(RuntimeError):
        codex.call_codex(
            "hi", {"type": "object", "properties": {}}, str(sys_f),
            codex_bin=fake_cli, codex_home=str(tmp_path / "empty_home"), root=str(tmp_path),
            quota_guard=None, timeout=60,
        )
    assert time.monotonic() - t0 < 10


def test_call_llm_codex_max_calls_maps_to_budget_exceeded(tmp_path):
    """S8: the per-module call cap is a BudgetExceededError and does not use up the after-reset pass."""
    lg = batch_driver.Ledger(str(tmp_path / "lg.jsonl"))
    lg.record("codex_call", provider="codex", model="gpt-6-luna", effort="low", usage={"input_tokens": 1})
    sys_f = tmp_path / "sys.txt"
    sys_f.write_text("RULES\n")
    guard = {"window_budget": 0.8, "after_reset": True, "slept_resets_at": time.time() - 10}
    with pytest.raises(batch_driver.BudgetExceededError):
        batch_driver._call_llm(
            "hi", {"type": "object", "properties": {}}, str(sys_f),
            provider="codex", stage="stage1", codex_bin=str(tmp_path / "no_such_codex"),
            codex_home=str(tmp_path / "empty_home"), codex_quota_guard=guard,
            ledger=lg, label="s8:stage1", max_calls=1,
        )
    assert guard["after_reset"] is True


def test_telemetry_garbage_and_missing_observed_at():
    """S3/S7: missing observed_at is not fresh; garbage values never crash and fail closed."""
    now = 2_000_000_000.0
    assert codex.is_window_fresh({"used_percent": 10, "resets_at": now + 100}, None, now=now) == (
        False, "observed_at missing")
    fresh, _msg = codex.is_window_fresh({"used_percent": 10, "resets_at": now + 100}, "garbage", now=now)
    assert not fresh
    fresh, _msg = codex.is_window_fresh({"used_percent": "lots", "resets_at": "soon"}, now - 5, now=now)
    assert not fresh
    norm = codex.normalize_rate_limits(
        {"primary": {"used_percent": "x", "resets_at": "y"}, "secondary": {"used_percent": 20, "resets_at": "zz"}},
        observed_at="not-a-date", source="test",
    )
    gate = codex.check_codex_quota_gate(norm, window_budget=0.8, now=now)
    assert gate["action"] == "error"
    garbage = {"observed_at": "x", "primary": {"used_percent": "a", "resets_at": "b"}, "secondary": "c"}
    assert codex.check_codex_quota_gate(garbage, window_budget=0.8, now=now)["action"] == "error"
    assert codex.check_codex_quota_gate(garbage, window_budget=1.0, now=now)["action"] == "ok"


def test_rollout_scan_skips_garbage_and_empty_cwd_guard(tmp_path):
    """S16/S13: garbage rollout lines/files and a dir named *.jsonl are skipped;
    the Codex cwd must be a real, empty directory."""
    home = tmp_path / "codex_home"
    day = home / "sessions" / "2026" / "11" / "22"
    day.mkdir(parents=True)
    now = time.time()
    ts = datetime.datetime.fromtimestamp(now - 30, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    valid = {
        "timestamp": ts, "type": "event_msg",
        "payload": {
            "type": "token_count", "info": {"total_token_usage": {"input_tokens": 1}},
            "rate_limits": {
                "primary": {"used_percent": 12, "window_minutes": 300, "resets_at": int(now + 3600)},
                "secondary": {"used_percent": 34, "window_minutes": 10080, "resets_at": int(now + 86400)},
            },
        },
    }
    (day / "a.jsonl").write_text("not json\n{\"broken\": \n[1,2]\n" + json.dumps(valid) + "\n{}\n")
    (day / "junk.jsonl").write_text("\x00\x01garbage\n{{{\n")
    (day / "x.jsonl").mkdir()
    rl = codex.read_latest_session_rate_limits(codex_home=str(home))
    assert rl and rl["primary"]["used_percent"] == 12.0 and rl["secondary"]["used_percent"] == 34.0

    root = tmp_path / "root"
    root.mkdir()
    d = codex._stable_empty_cwd(str(root))
    assert os.path.isdir(d) and os.listdir(d) == []
    (root / "build" / "driver" / "codex_empty_cwd" / "stray.txt").write_text("x")
    with pytest.raises(RuntimeError):
        codex._stable_empty_cwd(str(root))
    root2 = tmp_path / "root2"
    (root2 / "build" / "driver").mkdir(parents=True)
    target = tmp_path / "elsewhere"
    target.mkdir()
    os.symlink(target, root2 / "build" / "driver" / "codex_empty_cwd")
    with pytest.raises(RuntimeError):
        codex._stable_empty_cwd(str(root2))


def test_overnight_codex_dry_run_stubbed_queue_and_cli_args(tmp_path, monkeypatch, capsys):
    """N2: the Codex dry run works without war.exe and spawns nothing; build_cli_args
    forwards every Codex option."""
    repo = _git_repo(tmp_path)
    empty_home = tmp_path / "empty_home"
    empty_home.mkdir()
    monkeypatch.setattr(overnight, "path", lambda *parts: os.path.join(str(repo), *parts))
    monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(repo), "build", "live"))
    monkeypatch.setattr(overnight, "progress_done_count", lambda: (794, 1010, 414, 380))
    monkeypatch.setattr(overnight, "build_queue_with_needs_human", lambda **kw: ([_item()], []))
    spawned = []
    monkeypatch.setattr(overnight, "_run_subprocess_logged", lambda *a, **kw: spawned.append(a[0]) or (0, ""))
    rc = overnight.run_overnight(
        provider="codex", dry_run=True, window_budget=1.0, codex_home=str(empty_home), codex_repair_calls=0,
    )
    assert rc == 0 and spawned == []
    out = capsys.readouterr().out
    assert "DRY RUN [codex]" in out and "MOD_A" in out

    args = overnight.build_cli_args({
        "provider": "codex", "codex_bin": "/x/codex", "codex_home": "/h",
        "codex_max_total_calls": 5, "codex_max_7d_delta_pp": 10, "codex_max_7d_pct": 80,
        "codex_max_5h_pct": 70, "codex_telemetry_max_age": 600, "codex_early_stop_stage2": True,
        "codex_repair_calls": 2, "codex_stage2": "gpt-6.2-sol:low",
    })

    def val(flag):
        return args[args.index(flag) + 1]

    assert val("--provider") == "codex"
    assert val("--codex-bin") == "/x/codex" and val("--codex-home") == "/h"
    assert val("--codex-max-total-calls") == "5"
    assert val("--codex-max-7d-delta-pp") == "10" and val("--codex-max-7d-pct") == "80"
    assert val("--codex-max-5h-pct") == "70"
    assert val("--codex-telemetry-max-age") == "600"
    assert val("--codex-repair-calls") == "2"
    assert val("--codex-stage2") == "gpt-6.2-sol:low"
    assert "--codex-early-stop-stage2" in args
    # Claude config emits no Codex flags.
    assert not any(a.startswith("--codex") for a in overnight.build_cli_args({"window_budget": 0.8}))
