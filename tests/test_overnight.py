"""Unit and integration tests for wc1.overnight (live quota, metrics, controls, rollback, CLI)."""
import datetime
import json
import os
import stat
import subprocess
import sys
import threading
import time

import pytest

from wc1 import live, overnight, path


def test_window_budget_fraction_rules():
    assert not overnight.should_wait_for_window(1.0, 999.0, 35.0)
    assert not overnight.should_wait_for_window(0.8, 27.9, 35.0)
    assert overnight.should_wait_for_window(0.8, 28.0, 35.0)
    assert overnight.should_wait_for_window(0.5, 17.5, 35.0)
    with pytest.raises(ValueError):
        overnight.run_overnight(window_budget=0.0, dry_run=True)
    with pytest.raises(ValueError):
        overnight.run_overnight(window_budget=1.5, dry_run=True)


def test_check_window_budget_live_quota_and_fallback():
    now = 1_800_000_000.0
    rl = {
        "five_hour": {"utilization": 0.85, "resets_at": now + 1800, "status": "allowed"},
        "seven_day": {"utilization": 0.25, "resets_at": now + 86400, "status": "allowed"},
    }
    wait, secs, reason = overnight.check_window_budget(0.8, rl, 5.0, 35.0, now=now)
    assert wait
    assert 1800 <= secs <= 1900
    assert "85.0%" in reason

    # 1.0 budget does NOT pre-emptively pause when status is allowed
    wait2, _, _ = overnight.check_window_budget(1.0, rl, 34.0, 35.0, now=now)
    assert not wait2

    # Rejected status always pauses regardless of budget
    rl_rej = {
        "five_hour": {"utilization": 1.0, "resets_at": now + 600, "status": "rejected"},
    }
    wait3, secs3, _ = overnight.check_window_budget(1.0, rl_rej, 1.0, 35.0, now=now)
    assert wait3
    assert 600 <= secs3 <= 700

    # Stale resets_at falls back to rolling ledger
    rl_stale = {
        "five_hour": {"utilization": 0.99, "resets_at": now - 10, "status": "allowed"},
    }
    wait4, _, _ = overnight.check_window_budget(0.8, rl_stale, 10.0, 35.0, now=now)
    assert not wait4
    wait5, _, _ = overnight.check_window_budget(0.8, rl_stale, 29.0, 35.0, now=now)
    assert wait5


def test_parse_reset_text():
    # 2026-11-21 04:00 UTC == 08:00 Asia/Yerevan (UTC+4)
    now = datetime.datetime(2026, 11, 21, 4, 0, 0, tzinfo=datetime.timezone.utc).timestamp()
    ts = overnight.parse_reset_text("You've hit your 5-hour limit · resets 9:20am (Asia/Yerevan)", now=now)
    assert ts is not None
    # 9:20am Asia/Yerevan = 05:20 UTC = now + 80m
    assert abs((ts - now) - 80 * 60) < 2.0


def test_rolling_window_spend_and_ledger_metrics(tmp_path):
    now = 1_700_000_000.0
    iso = lambda t: datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lg = tmp_path / "a.jsonl"
    rows = [
        {"ts": iso(now - 6 * 3600), "stage": "claude_call", "cost_usd": 10.0},  # >5h, <7d
        {"ts": iso(now - 2 * 3600), "stage": "claude_call", "cost_usd": 1.25,
         "usage": {"input_tokens": 100, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 800}},
        {"ts": iso(now - 100), "stage": "claude_call", "cost_usd": 0.75,
         "usage": {"input_tokens": 50, "cache_creation_input_tokens": 50, "cache_read_input_tokens": 900}},
        {"ts": iso(now - 50), "stage": "stage4_done", "cost_usd": 99.0},
    ]
    lg.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    spend, calls, oldest = overnight.rolling_window_spend(str(tmp_path), now=now)
    assert spend == 2.0
    assert calls == 2
    assert abs(oldest - (now - 2 * 3600)) < 1.0
    assert abs(overnight.compute_wait_seconds(oldest, now=now) - (3 * 3600 + 90)) <= 1

    m = overnight.ledger_metrics(str(tmp_path), now=now, buckets=10)
    assert m["spend_5h"] == 2.0
    assert m["spend_7d"] == 12.0
    assert m["calls_7d"] == 3
    assert m["burn_rate_usd_per_h"] == 0.75
    assert m["cache_hit_pct"] == 85.0
    assert len(m["sparkline"]) == 10
    assert abs(sum(m["sparkline"]) - 2.0) < 1e-3


def test_parse_git_porcelain_ignores_build_and_original():
    sample = (
        " M analysis/symbols/audio.toml\n"
        "?? src/foo/bar.c\n"
        "?? build/overnight.log\n"
        "?? original/war.exe\n"
        "A  tests/test_foo.py\n"
    )
    tracked, untracked = overnight.parse_git_porcelain(sample)
    assert tracked == {"analysis/symbols/audio.toml", "tests/test_foo.py"}
    assert untracked == {"src/foo/bar.c"}


def test_archive_and_rollback_preserves_baseline_untracked(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "tracked.txt").write_text("orig\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    (tmp_path / "wip_keep.txt").write_text("precious\n")
    (tmp_path / "tracked.txt").write_text("broken\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "new_mod.c").write_text("int x;\n")

    arch = overnight.archive_and_rollback(
        "demo", {"tracked.txt"}, {"src/new_mod.c"}, log_text="boom", cwd=str(tmp_path),
    )
    assert (tmp_path / "tracked.txt").read_text() == "orig\n"
    assert not (tmp_path / "src" / "new_mod.c").exists()
    assert (tmp_path / "wip_keep.txt").read_text() == "precious\n"
    assert os.path.isfile(os.path.join(arch, "src", "new_mod.c"))
    assert os.path.isfile(os.path.join(arch, "failure.log"))


def test_progress_done_count_counts_uppercase_t3_t4():
    if not os.path.exists(path("original", "install", "war.exe")):
        pytest.skip("needs original/install/war.exe")
    done, total, t3, t4 = overnight.progress_done_count()
    assert total > 0
    assert t3 > 0
    assert t4 > 0
    # done requires both named and T3/T4, so done <= t3 + t4
    assert t3 <= done <= t3 + t4


def test_build_cli_args_and_launcher_routing():
    cfg = {
        "window_budget": 1.0, "window_capacity": 35.0, "max_modules": 5,
        "wave": "wave3", "chunk_size": 10, "module_budget": 1.25,
        "module_calls": 8, "repair_budget": 0.30,
        "skip": ("BULLET.C", "STATUS.C"), "only": ("mod_19b80",),
        "sleep_on_limit": False, "rate_limit_sleep": 600,
    }
    args = overnight.build_cli_args(cfg)
    assert "--headless" in args
    assert "--no-sleep" in args
    ap = overnight._build_parser()
    parsed = ap.parse_args(args)
    assert parsed.headless is True
    assert parsed.window_budget == 1.0
    assert parsed.max_modules == 5
    assert parsed.wave == "wave3"
    assert parsed.only == "mod_19b80"
    assert parsed.no_sleep is True

    # Launcher opens ONLY on empty argv + interactive TTY
    p_empty = ap.parse_args([])
    assert overnight.should_open_launcher([], p_empty, is_tty=True)
    assert not overnight.should_open_launcher([], p_empty, is_tty=False)
    p_dry = ap.parse_args(["--dry-run"])
    assert not overnight.should_open_launcher(["--dry-run"], p_dry, is_tty=True)
    p_head = ap.parse_args(["--headless"])
    assert not overnight.should_open_launcher(["--headless"], p_head, is_tty=True)


def test_controller_pause_resume_wake_and_graceful_stop(tmp_path):
    root = str(tmp_path)
    ctrl = overnight._RunController({"window_budget": 1.0}, (100, 1010, 50, 50), root=root)
    log_p = tmp_path / "run.log"

    # Pause -> Resume
    live.send_control("pause", root=root)
    ctrl.poll_control()
    assert ctrl.pause_requested

    def _resume_soon():
        time.sleep(0.3)
        live.send_control("resume", root=root)

    t = threading.Thread(target=_resume_soon, daemon=True)
    t.start()
    with open(log_p, "w") as lf:
        overnight._wait_while_paused(lf, ctrl)
    t.join(timeout=2.0)
    assert not ctrl.pause_requested
    assert ctrl.status == "RUNNING"

    # Sleep -> Early Wake
    def _wake_soon():
        time.sleep(0.3)
        live.send_control("wake", root=root)

    t2 = threading.Thread(target=_wake_soon, daemon=True)
    t2.start()
    t0 = time.time()
    with open(log_p, "a") as lf:
        overnight._sleep_with_heartbeat(30, "test sleep", lf, controller=ctrl)
    t2.join(timeout=2.0)
    assert time.time() - t0 < 5.0

    # Graceful Stop
    live.send_control("graceful_stop", root=root)
    ctrl.poll_control()
    assert ctrl.stop_requested
    st = live.read_json(live.state_path(root=root))
    assert st["stop_requested"] is True


def test_immediate_kill_terminates_child_tree(tmp_path):
    root = str(tmp_path)
    ctrl = overnight._RunController({"window_budget": 1.0}, (100, 1010, 50, 50), root=root)
    child_pid_file = tmp_path / "grandchild.pid"
    script = tmp_path / "hang.py"
    script.write_text(
        "import subprocess, sys, time\n"
        "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        f"open({str(child_pid_file)!r}, 'w').write(str(p.pid))\n"
        "time.sleep(60)\n"
    )

    def _kill_soon():
        time.sleep(0.45)
        live.send_control("kill", root=root)

    t = threading.Thread(target=_kill_soon, daemon=True)
    t.start()
    with open(tmp_path / "run.log", "w") as lf:
        with pytest.raises(overnight.ImmediateKillError):
            overnight._run_subprocess_logged(
                [sys.executable, str(script)], lf, cwd=root, controller=ctrl,
            )
    t.join(timeout=2.0)
    if child_pid_file.exists():
        gpid = int(child_pid_file.read_text().strip())
        deadline = time.time() + 2.0
        while live.pid_alive(gpid) and time.time() < deadline:
            time.sleep(0.05)
        assert not live.pid_alive(gpid)


def test_run_overnight_graceful_stop_and_immediate_kill_e2e(tmp_path, monkeypatch):
    """End-to-end mocked run_overnight verifying graceful_stop finishes active module
    and immediate kill terminates child + rolls back ONLY active module changes."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("orig\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    # Pre-existing untracked WIP that MUST NEVER be touched
    (repo / "preexisting_wip.c").write_text("/* keep */\n")

    def fake_path(*parts):
        return os.path.join(str(repo), *parts)

    monkeypatch.setattr(overnight, "path", fake_path)
    monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(repo), "build", "live"))

    queue_items = [
        {"key": ("c-only", "MOD_A", 0), "mode": "c-only", "module": "MOD_A", "area": "mod_a_c",
         "src_subdir": "mod_a", "header": None, "limit": None, "count": 2, "addrs": [0x1000, 0x1010],
         "module_total": 2, "total_insns": 20, "avg_insns": 10.0},
        {"key": ("c-only", "MOD_B", 0), "mode": "c-only", "module": "MOD_B", "area": "mod_b_c",
         "src_subdir": "mod_b", "header": None, "limit": None, "count": 2, "addrs": [0x2000, 0x2010],
         "module_total": 2, "total_insns": 20, "avg_insns": 10.0},
    ]
    prog_counter = {"done": 600}
    monkeypatch.setattr(overnight, "progress_done_count",
                        lambda: (prog_counter["done"], 1010, prog_counter["done"] // 2, prog_counter["done"] // 2))

    # --- Case 1: graceful_stop during MOD_A finishes MOD_A, commits, does NOT run MOD_B ---
    ran_modules = []
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: list(queue_items[len(ran_modules):]))

    def fake_subproc_graceful(cmd, log_fh, cwd=None, controller=None, worker_id=None, event_kind="info"):
        if cmd[0] == sys.executable:
            mod = cmd[4]
            ran_modules.append(mod)
            (repo / "mod_a.c").write_text("int a(void) { return 1; }\n")
            prog_counter["done"] += 2
            live.send_control("graceful_stop")
            if controller:
                controller.poll_control()
            return 0, "ok\n"
        # make verify
        return 0, "IDENTICAL\n100 passed\n"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", fake_subproc_graceful)
    rc = overnight.run_overnight(window_budget=1.0, repair_budget=0.0)
    assert rc == 0
    assert ran_modules == ["MOD_A"]
    assert (repo / "mod_a.c").exists()
    assert (repo / "preexisting_wip.c").exists()
    st = live.read_json(live.state_path())
    assert st["status"] == "DONE"
    assert len(st["commits"]) == 1

    # --- Case 2: immediate kill during MOD_B rolls back MOD_B edits & preserves WIP ---
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [queue_items[1]])

    def fake_subproc_kill(cmd, log_fh, cwd=None, controller=None, worker_id=None, event_kind="info"):
        (repo / "tracked.txt").write_text("dirty during kill\n")
        (repo / "mod_b_temp.c").write_text("int b(void) { return 2; }\n")
        raise overnight.ImmediateKillError("user kill")

    monkeypatch.setattr(overnight, "_run_subprocess_logged", fake_subproc_kill)
    rc2 = overnight.run_overnight(window_budget=1.0, repair_budget=0.0)
    assert rc2 == 143
    assert (repo / "tracked.txt").read_text() == "orig\n"
    assert not (repo / "mod_b_temp.c").exists()
    assert (repo / "preexisting_wip.c").read_text() == "/* keep */\n"
    st2 = live.read_json(live.state_path())
    assert st2["status"] == "KILLED"


def test_default_skip_includes_playflic():
    assert "PLAYFLIC.C" in overnight.DEFAULT_SKIP
    assert "BULLET.C" in overnight.DEFAULT_SKIP
    assert "STATUS.C" in overnight.DEFAULT_SKIP
    if os.path.exists(path("original", "install", "war.exe")):
        q = overnight.build_queue(wave="all")
        assert all(it["module"] != "PLAYFLIC.C" for it in q)


def test_is_repair_rate_limited_ignores_allowed_events_and_clean_success():
    # Allowed rate_limit_event with normal result must NEVER trip rl_hit
    assert not overnight._rate_limit_event_rejected(
        {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "utilization": 0.42}}
    )
    assert overnight._rate_limit_event_rejected(
        {"type": "rate_limit_event", "rate_limit_info": {"status": "rejected", "utilization": 1.0}}
    )
    ok_res = {"type": "result", "is_error": False, "result": "Fixed test at 0x429; disk quota ok."}
    assert not overnight._is_repair_rate_limited(0, ok_res, "", rl_rejected=False)
    # Clean rc==0 non-error repair must NOT roll back even if one quota window reported rejected
    assert not overnight._is_repair_rate_limited(0, ok_res, "", rl_rejected=True)
    # Isolated rl_rejected with rc=1 and neutral error text MUST trigger rate-limit
    neutral_err = {"type": "result", "is_error": True, "result": "Request failed."}
    assert overnight._is_repair_rate_limited(1, neutral_err, "", rl_rejected=True)
    # Word-bounded regexes reject false positives ("0x429", "disk quota", bare "overloaded")
    fp_err = {"type": "result", "is_error": True, "result": "Address 0x429 failed; disk quota; overloaded fn"}
    assert not overnight._is_repair_rate_limited(1, fp_err, "", rl_rejected=False)
    # Real rate limit error messages trigger
    err_res = {"type": "result", "is_error": True, "result": "You've hit your 5-hour limit · resets 9am"}
    assert overnight._is_repair_rate_limited(1, err_res, "", rl_rejected=False)
    assert overnight._is_repair_rate_limited(1, None, "Error 429: rate limit exceeded", rl_rejected=False)


def test_run_bounded_repair_does_not_false_positive_on_allowed_rate_limit_event(tmp_path, monkeypatch):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_claude = fake_bin / "claude"
    fake_claude.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        "print(json.dumps({'type': 'rate_limit_event', 'rate_limit_info': {'status': 'allowed', 'utilization': 0.25}}))\n"
        "print(json.dumps({'type': 'result', 'is_error': False, 'total_cost_usd': 0.12, 'result': 'Repaired cleanly.'}))\n"
    )
    fake_claude.chmod(fake_claude.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{fake_bin}:{os.environ.get('PATH', '')}")

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(overnight, "path", lambda *parts: os.path.join(str(repo), *parts))
    monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(repo), "build", "live"))

    item = {"module": "DEMO.C", "mode": "c-only", "area": "demo_c"}
    with open(tmp_path / "run.log", "w") as lf:
        ok, cost, rl_hit, txt = overnight.run_bounded_repair(
            item, ["tests/test_demo.py"], "1 failed", 0.45, lf,
        )
    assert ok is True
    assert rl_hit is False
    assert abs(cost - 0.12) < 1e-6
    assert "Repaired cleanly." in txt

    # Isolated rejected rate_limit_event with neutral text & rc=1 DOES trip rl_hit and records partial cost
    fake_claude.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "print(json.dumps({'type': 'rate_limit_event', 'rate_limit_info': {'status': 'rejected', 'utilization': 1.0}}))\n"
        "print(json.dumps({'type': 'result', 'is_error': True, 'total_cost_usd': 0.03, 'result': 'Request blocked.'}))\n"
        "sys.exit(1)\n"
    )
    with open(tmp_path / "run.log", "a") as lf:
        ok2, cost2, rl_hit2, _txt2 = overnight.run_bounded_repair(
            item, ["tests/test_demo.py"], "1 failed", 0.45, lf,
        )
    assert ok2 is False
    assert rl_hit2 is True
    assert abs(cost2 - 0.03) < 1e-6


def test_ledger_is_resumable_filters_stale_finished_and_exhausted(tmp_path):
    from wc1 import batch_driver

    # Non-existent or empty ledger -> not resumable
    assert not overnight._ledger_is_resumable(str(tmp_path / "missing.jsonl"))
    p_empty = tmp_path / "empty.jsonl"
    p_empty.write_text("")
    assert not overnight._ledger_is_resumable(str(p_empty), module_budget=1.10, module_calls=10)

    # Mid-flight rate_limit or claude_timeout under budget -> resumable
    p_rl = tmp_path / "rl.jsonl"
    lg = batch_driver.Ledger(str(p_rl))
    lg.record("claude_call", cost_usd=0.40)
    lg.record("rate_limit", reason="5h")
    assert overnight._ledger_is_resumable(str(p_rl), module_budget=1.10, module_calls=10)
    # Over budget -> NOT resumable
    assert not overnight._ledger_is_resumable(str(p_rl), module_budget=0.35, module_calls=10)
    # Over calls -> NOT resumable
    assert not overnight._ledger_is_resumable(str(p_rl), module_budget=1.10, module_calls=1)

    p_to = tmp_path / "to.jsonl"
    lgto = batch_driver.Ledger(str(p_to))
    lgto.record("claude_call", cost_usd=0.20)
    lgto.record("claude_timeout", reason="timeout")
    assert overnight._ledger_is_resumable(str(p_to), module_budget=1.10, module_calls=10)

    # Finished / failed / rolled_back -> NOT resumable
    for terminal in ("stage4_done", "stage4_fail", "rolled_back"):
        p_t = tmp_path / f"{terminal}.jsonl"
        lgt = batch_driver.Ledger(str(p_t))
        lgt.record("claude_call", cost_usd=0.20)
        lgt.record(terminal, ok=(terminal == "stage4_done"))
        assert not overnight._ledger_is_resumable(str(p_t), module_budget=1.10, module_calls=10)


def test_verify_staged_toml_refs_catches_untracked_c_file(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "analysis" / "symbols").mkdir(parents=True)
    (tmp_path / "src" / "demo").mkdir(parents=True)
    (tmp_path / "src" / "demo" / "ok.c").write_text("int ok(void) { return 0; }\n")
    (tmp_path / "src" / "demo" / "orphan.c").write_text("int orphan(void) { return 1; }\n")
    toml_p = tmp_path / "analysis" / "symbols" / "demo.toml"
    toml_p.write_text(
        '[[func]]\naddr = 0x1000\nname = "Ok"\nsrc = "src/demo/ok.c"\n'
        '[[func]]\naddr = 0x1010\nname = "Orphan"\nref = "src/demo/orphan.c"\n'
    )
    subprocess.run(["git", "add", "src/demo/ok.c"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    # Missing orphan.c (untracked and not in changed_paths)
    missing = overnight._verify_staged_toml_refs({"analysis/symbols/demo.toml"}, cwd=str(tmp_path))
    assert missing == ["src/demo/orphan.c"]
    # Present once included in changed_paths
    assert overnight._verify_staged_toml_refs(
        {"analysis/symbols/demo.toml", "src/demo/orphan.c"}, cwd=str(tmp_path),
    ) == []


def test_run_overnight_repair_rl_retries_and_interrupt_cleans_tree(tmp_path, monkeypatch):
    """Verify:
    1) Repair rate-limit sleeps and retries repair on the SAME tree; second failure archives & rolls back.
    2) batch_driver EXIT_RATE_LIMIT resumes exact item with preserved last_clean_done.
    3) KeyboardInterrupt and unhandled Exception archive & roll back dirty files cleanly.
    4) --no-sleep on must_wait does NOT mark an unstarted ledger rolled_back."""
    from wc1 import batch_driver

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("orig\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)

    monkeypatch.setattr(overnight, "path", lambda *parts: os.path.join(str(repo), *parts))
    monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(repo), "build", "live"))
    monkeypatch.setattr(overnight, "_sleep_with_heartbeat", lambda *a, **kw: None)

    item_a = {
        "key": ("c-only", "MOD_A", 0), "mode": "c-only", "module": "MOD_A", "area": "mod_a_c",
        "src_subdir": "mod_a", "header": None, "limit": None, "count": 1, "addrs": [0x1000],
        "module_total": 1, "total_insns": 10, "avg_insns": 10.0,
    }
    item_b = {
        "key": ("c-only", "MOD_B", 0), "mode": "c-only", "module": "MOD_B", "area": "mod_b_c",
        "src_subdir": "mod_b", "header": None, "limit": None, "count": 1, "addrs": [0x2000],
        "module_total": 1, "total_insns": 10, "avg_insns": 10.0,
    }

    # --- Case 1: repair hits rate limit twice -> archived & rolled back, never leaked ---
    q_calls = {"n": 0}
    def q_case1(**kw):
        q_calls["n"] += 1
        return [item_a] if q_calls["n"] == 1 else []

    monkeypatch.setattr(overnight, "build_queue", q_case1)
    monkeypatch.setattr(overnight, "progress_done_count", lambda: (600, 1010, 300, 300))
    repair_calls = {"n": 0}

    def subproc_case1(cmd, log_fh, cwd=None, controller=None, worker_id=None, event_kind="info"):
        if cmd[0] == sys.executable:
            (repo / "tracked.txt").write_text("dirty from repair rl\n")
            (repo / "src" / "mod_a").mkdir(parents=True, exist_ok=True)
            (repo / "src" / "mod_a" / "leaked.c").write_text("int leak;\n")
            batch_driver.Ledger(os.path.join(str(repo), "build", "ledger", "mod_a_c.jsonl")).record(
                "claude_call", cost_usd=0.10,
            )
            return 0, "ok\n"
        return 1, "1 failed\n"

    def fake_repair_rl(*a, **kw):
        repair_calls["n"] += 1
        return False, 0.0, True, "rate limited"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", subproc_case1)
    monkeypatch.setattr(overnight, "run_bounded_repair", fake_repair_rl)
    assert overnight.run_overnight(window_budget=1.0, repair_budget=0.45, sleep_on_limit=True) == 0
    assert repair_calls["n"] == 2  # retried once on same tree before archiving
    assert (repo / "tracked.txt").read_text() == "orig\n"
    assert not (repo / "src" / "mod_a" / "leaked.c").exists()
    assert not (repo / "src" / "mod_a").exists()  # empty subdir pruned
    assert any(p.name.endswith("_mod_a_c") for p in (repo / "build" / "failed").iterdir())
    assert not overnight._ledger_is_resumable(os.path.join(str(repo), "build", "ledger", "mod_a_c.jsonl"))

    # --- Case 2: batch_driver hits EXIT_RATE_LIMIT after drafting TOML (done rises before wake) ---
    prog = {"done": 600}
    monkeypatch.setattr(overnight, "progress_done_count", lambda: (prog["done"], 1010, 300, prog["done"] - 300))
    runs = {"b": 0}
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [item_b] if runs["b"] == 0 else [])

    def subproc_case2(cmd, log_fh, cwd=None, controller=None, worker_id=None, event_kind="info"):
        if cmd[0] == sys.executable:
            runs["b"] += 1
            if runs["b"] == 1:
                (repo / "mod_b.c").write_text("int b(void) { return 1; }\n")
                prog["done"] = 601
                return batch_driver.EXIT_RATE_LIMIT, "[RATE_LIMIT] 5h limit\n"
            return 0, "resumed ok\n"
        return 0, "IDENTICAL\n100 passed\n"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", subproc_case2)
    assert overnight.run_overnight(window_budget=1.0, repair_budget=0.0, sleep_on_limit=True) == 0
    assert runs["b"] == 2
    assert (repo / "mod_b.c").exists()
    st = live.read_json(live.state_path())
    assert len(st["commits"]) == 1
    assert st["commits"][0]["delta"] == 1

    # --- Case 3: KeyboardInterrupt and RuntimeError archive & roll back dirty tree ---
    for exc_cls, expect_rc in ((KeyboardInterrupt, 130), (RuntimeError, None)):
        monkeypatch.setattr(overnight, "build_queue", lambda **kw: [item_a])

        def subproc_boom(cmd, log_fh, cwd=None, controller=None, worker_id=None, event_kind="info", exc_cls=exc_cls):
            (repo / "tracked.txt").write_text("dirty before crash\n")
            (repo / "temp_crash.c").write_text("int crash;\n")
            raise exc_cls("boom")

        monkeypatch.setattr(overnight, "_run_subprocess_logged", subproc_boom)
        if expect_rc is not None:
            assert overnight.run_overnight(window_budget=1.0, repair_budget=0.0) == expect_rc
        else:
            with pytest.raises(RuntimeError):
                overnight.run_overnight(window_budget=1.0, repair_budget=0.0)
        assert (repo / "tracked.txt").read_text() == "orig\n"
        assert not (repo / "temp_crash.c").exists()

    # --- Case 4: --no-sleep on must_wait leaves an unstarted resumable ledger untouched ---
    lg_path = os.path.join(str(repo), "build", "ledger", "mod_c_c.jsonl")
    lg_c = batch_driver.Ledger(lg_path)
    lg_c.record("claude_call", cost_usd=0.20)
    lg_c.record("rate_limit", reason="5h")
    item_c = dict(item_a, module="MOD_C", area="mod_c_c")
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [item_c])
    monkeypatch.setattr(overnight, "check_window_budget", lambda *a, **kw: (True, 600, "budget full"))
    assert overnight.run_overnight(window_budget=0.8, repair_budget=0.0, sleep_on_limit=False) == 0
    assert overnight._ledger_is_resumable(lg_path, module_budget=1.10, module_calls=10)


def test_overnight_dry_run():
    if not os.path.exists(path("original", "install", "war.exe")):
        pytest.skip("needs original/install/war.exe")
    rc = overnight.main(["--dry-run", "--window-budget", "1.0", "--max-modules", "5"])
    assert rc == 0


def test_build_queue_with_needs_human_filters_unautomatable():
    if not os.path.exists(path("original", "install", "war.exe")):
        pytest.skip("needs original/install/war.exe")
    items, needs_human = overnight.build_queue_with_needs_human(wave="all")
    queued_addrs = {a for it in items for a in it["addrs"]}
    nh_by_addr = {nh["addr"]: nh["reason"] for nh in needs_human}
    # Data-in-code starts must NEVER be queued
    for a in (0x110a0, 0x11530):
        assert a not in queued_addrs
        assert a in nh_by_addr and "data-in-code" in nh_by_addr[a]
    # codegen_promo.toml entries must NEVER be queued
    for a in (0x1132c, 0x13e94, 0x15170):
        assert a not in queued_addrs
        assert a in nh_by_addr and "locked TOML" in nh_by_addr[a]
    # Already-matched unbuildable T3s must NEVER be queued
    for a in (0x2efd0, 0x2f73c):
        assert a not in queued_addrs
        assert a in nh_by_addr and "unbuildable T3" in nh_by_addr[a]
    # Name-only (already has C) and existing low/placeholder entries in other TOMLs must NEVER be queued
    for a in (0x26360, 0x2b308, 0x257dc):
        assert a not in queued_addrs
        assert a in nh_by_addr


def test_commit_gate_no_regression_and_path_allowlist(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "analysis" / "symbols").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "analysis" / "symbols" / "owner.toml").write_text("# owner\n")
    (tmp_path / "tests" / "test_existing.py").write_text("def test_x(): pass\n")
    subprocess.run(["git", "add", "analysis/symbols/owner.toml", "tests/test_existing.py"],
                   cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    # No-regression checks
    before = {
        0x1000: {"done": True, "c": "T3", "src": "src/a/f.c", "ref": None, "ref_verified_by": None, "name": "Foo"},
        0x1010: {"done": True, "c": "T4", "src": None, "ref": "src/a/g_ref.c", "ref_verified_by": "difftest: t::g", "name": "Bar"},
    }
    # T4 -> T3 promotion is NOT a regression
    after_ok = {
        0x1000: dict(before[0x1000]),
        0x1010: {"done": True, "c": "T3", "src": "src/a/g.c", "ref": None, "ref_verified_by": None, "name": "Bar"},
    }
    assert overnight._check_no_regression(before, after_ok) == []
    # Dropping src= IS a regression
    after_bad = {
        0x1000: {"done": False, "c": "none", "src": None, "ref": None, "ref_verified_by": None, "name": "Foo"},
        0x1010: dict(before[0x1010]),
    }
    regs = overnight._check_no_regression(before, after_bad)
    assert any("0x1000" in r and "lost src" in r for r in regs)

    # Path allowlist
    item = {"area": "demo_c", "src_subdir": "demo", "header": "src/include/demo.h"}
    good = [
        "analysis/symbols/demo_c.toml",
        "analysis/symbols/owner.toml",
        "src/demo/foo.c",
        "src/include/demo.h",
        "docs/subsystems/demo_c.md",
        "tests/test_demo_c.py",
    ]
    assert overnight._check_allowed_paths(good, item, owned_tomls=["analysis/symbols/owner.toml"], cwd=str(tmp_path)) == []
    bad = [
        "Makefile",
        "tools/wc1/overnight.py",
        "src/include/war.h",
        "analysis/symbols/codegen_promo.toml",
        "analysis/symbols/other.toml",
        "tests/test_existing.py",
        "src/other/x.c",
    ]
    disallowed = overnight._check_allowed_paths(bad, item, owned_tomls=["analysis/symbols/owner.toml"], cwd=str(tmp_path))
    assert set(disallowed) == set(bad)


def test_wire_verified_t4_after_repair_and_verify_new_ref_verified_by(tmp_path):
    from wc1 import batch_driver
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "analysis" / "symbols").mkdir(parents=True)
    (tmp_path / "src" / "demo").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "build" / "ledger").mkdir(parents=True)

    (tmp_path / "src" / "demo" / "foo_reference.c").write_text("void Foo(void) {}\n")
    (tmp_path / "src" / "demo" / "bar_reference.c").write_text("void Bar(void) {}\n")
    toml_p = tmp_path / "analysis" / "symbols" / "demo_c.toml"
    toml_p.write_text(
        '[[func]]\naddr = 0x1000\nname = "Foo"\nconv = "watcall"\nconfidence = "high"\n'
        'evidence = ["e"]\nref = "src/demo/foo_reference.c"\nt3_blocker = "regalloc: x"\n\n'
        '[[func]]\naddr = 0x1010\nname = "Bar"\nconv = "watcall"\nconfidence = "high"\n'
        'evidence = ["e"]\nref = "src/demo/bar_reference.c"\nt3_blocker = "regalloc: y"\n'
    )
    (tmp_path / "tests" / "test_demo_c.py").write_text(
        "def test_foo():\n"
        "    # t4spec.run_spec('src/demo/foo_reference.c')\n"
        "    assert True\n"
        "def test_bar():\n"
        "    # t4spec.run_spec('src/demo/bar_reference.c')\n"
        "    assert False\n"
    )
    lg = batch_driver.Ledger(str(tmp_path / "build" / "ledger" / "demo_c.jsonl"))
    # Stale entry before rolled_back MUST be ignored
    lg.record("stage4_pending", test_path="tests/test_old.py", pending_ref_verified_by={
        "0x1010": "difftest: tests/test_demo_c.py::test_foo",
    })
    lg.record("rolled_back", reason="old_fail", ok=False)
    lg.record("target_addrs", addrs=["0x1000", "0x1010"])
    lg.record("stage4_pending", test_path="tests/test_demo_c.py", pending_ref_verified_by={
        "0x1000": "difftest: tests/test_demo_c.py::test_foo",
        "0x1010": "difftest: tests/test_demo_c.py::test_bar",
    })

    wired = overnight._wire_verified_t4_after_repair("demo_c", cwd=str(tmp_path))
    assert wired == {0x1000: "difftest: tests/test_demo_c.py::test_foo"}
    txt = toml_p.read_text()
    assert 'ref_verified_by = "difftest: tests/test_demo_c.py::test_foo"' in txt
    assert "test_bar" not in txt
    # Commit-gate verifier accepts the newly wired passing node
    errs = overnight._verify_new_ref_verified_by(
        {}, {"analysis/symbols/demo_c.toml", "tests/test_demo_c.py"}, cwd=str(tmp_path),
    )
    assert errs == []
    # _verify_staged_toml_refs also checks missing C file in verified_by = "match: ..."
    (tmp_path / "analysis" / "symbols" / "unb.toml").write_text(
        '[[func]]\naddr = 0x2000\nname = "U"\nconfidence = "verified"\n'
        'verified_by = "match: python3 -m wc1.match src/demo/missing_unbuildable.c"\n'
        'evidence = ["e"]\n'
    )
    assert overnight._verify_staged_toml_refs({"analysis/symbols/unb.toml"}, cwd=str(tmp_path)) == [
        "src/demo/missing_unbuildable.c"
    ]


def test_run_overnight_passes_addrs_and_rejects_disallowed_path(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "Makefile").write_text("all:\n\t@true\n")
    (repo / "analysis" / "symbols").mkdir(parents=True)
    (repo / "analysis" / "symbols" / "seed.toml").write_text("# seed\n")
    subprocess.run(["git", "add", "Makefile", "analysis/symbols/seed.toml"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)

    monkeypatch.setattr(overnight, "path", lambda *parts: os.path.join(str(repo), *parts))
    monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(repo), "build", "live"))
    item = {
        "key": ("c-only", "MOD_A", 0), "mode": "c-only", "module": "MOD_A", "area": "mod_a_c",
        "src_subdir": "mod_a", "header": None, "limit": None, "count": 2, "addrs": [0x1000, 0x1010],
        "module_total": 2, "total_insns": 20, "avg_insns": 10.0,
    }
    seen_cmds = []
    done_box = {"n": 600}
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [item] if not seen_cmds else [])
    monkeypatch.setattr(overnight, "progress_done_count", lambda: (done_box["n"], 1010, 300, done_box["n"] - 300))

    def fake_subproc(cmd, log_fh, cwd=None, controller=None, worker_id=None, event_kind="info"):
        if cmd[0] == sys.executable:
            seen_cmds.append(list(cmd))
            (repo / "Makefile").write_text("all:\n\t@false\n")
            done_box["n"] = 601
            return 0, "ok\n"
        return 0, "IDENTICAL\n100 passed\n"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", fake_subproc)
    rc = overnight.run_overnight(window_budget=1.0, repair_budget=0.0)
    assert rc == 0
    assert seen_cmds and "--addrs" in seen_cmds[0]
    assert seen_cmds[0][seen_cmds[0].index("--addrs") + 1] == "0x1000,0x1010"
    # Disallowed Makefile edit must be rolled back and NOT committed
    assert (repo / "Makefile").read_text() == "all:\n\t@true\n"
    st = live.read_json(live.state_path())
    assert len(st["commits"]) == 0
    assert st["completed"][0]["status"] == "FAILED"
    assert "disallowed paths" in st["completed"][0]["note"]
