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


def test_overnight_dry_run():
    if not os.path.exists(path("original", "install", "war.exe")):
        pytest.skip("needs original/install/war.exe")
    rc = overnight.main(["--dry-run", "--window-budget", "1.0", "--max-modules", "5"])
    assert rc == 0
