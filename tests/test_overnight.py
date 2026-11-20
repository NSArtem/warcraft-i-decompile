"""Unit tests for wc1.overnight (fractional window budget, rolling spend, git rollback, dry-run)."""
import json
import os
import subprocess
import time

import pytest

from wc1 import overnight, path


def test_window_budget_fraction_rules():
    # 1.0 = spend entire window until actual rate limit (never pre-emptively pause)
    assert not overnight.should_wait_for_window(1.0, 999.0, 35.0)
    # 0.8 of $35 = $28 threshold
    assert not overnight.should_wait_for_window(0.8, 27.9, 35.0)
    assert overnight.should_wait_for_window(0.8, 28.0, 35.0)
    assert overnight.should_wait_for_window(0.5, 17.5, 35.0)
    with pytest.raises(ValueError):
        overnight.run_overnight(window_budget=0.0, dry_run=True)
    with pytest.raises(ValueError):
        overnight.run_overnight(window_budget=1.5, dry_run=True)


def test_rolling_window_spend_filters_by_5h(tmp_path):
    now = 1_700_000_000.0
    import datetime
    iso = lambda t: datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lg = tmp_path / "a.jsonl"
    rows = [
        {"ts": iso(now - 6 * 3600), "stage": "claude_call", "cost_usd": 10.0},  # expired
        {"ts": iso(now - 2 * 3600), "stage": "claude_call", "cost_usd": 1.25},
        {"ts": iso(now - 100), "stage": "claude_call", "cost_usd": 0.75},
        {"ts": iso(now - 50), "stage": "stage4_done", "cost_usd": 99.0},        # not a claude_call
    ]
    lg.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    spend, calls, oldest = overnight.rolling_window_spend(str(tmp_path), now=now)
    assert spend == 2.0
    assert calls == 2
    assert abs(oldest - (now - 2 * 3600)) < 1.0
    # Wait seconds until oldest ages out past 5h + 90s margin = 3h + 90s
    assert abs(overnight.compute_wait_seconds(oldest, now=now) - (3 * 3600 + 90)) <= 1


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

    # Pre-existing untracked WIP (like BULLET.C)
    (tmp_path / "wip_keep.txt").write_text("precious\n")
    # Simulated module edits
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


def test_overnight_dry_run():
    if not os.path.exists(path("original", "install", "war.exe")):
        pytest.skip("needs original/install/war.exe")
    rc = overnight.main(["--dry-run", "--window-budget", "1.0", "--max-modules", "5"])
    assert rc == 0
