"""Unit and Textual Pilot UI tests for wc1.tui (dashboard, launcher, heatmap, stream, controls)."""
import asyncio
import json
import os
import subprocess
import sys
import time

import pytest

from wc1 import live, overnight, tui


def _sample_fn_rows():
    return [
        {"addr": 0x1000, "name": "FooT3", "module": "MOD_A", "scope": "in", "named": True, "c": "T3", "done": True, "src": "src/a/foo.c"},
        {"addr": 0x1020, "name": "FooT4", "module": "MOD_A", "scope": "in", "named": True, "c": "T4", "done": True, "src": "src/a/bar_reference.c"},
        {"addr": 0x1040, "name": "FooRef", "module": "MOD_B", "scope": "in", "named": True, "c": "ref", "done": False, "src": "src/b/ref.c"},
        {"addr": 0x1060, "name": "FooNamed", "module": "MOD_B", "scope": "in", "named": True, "c": "none", "done": False, "src": ""},
        {"addr": 0x1080, "name": "fn_01080", "module": "MOD_C", "scope": "in", "named": False, "c": "none", "done": False, "src": ""},
        {"addr": 0x10a0, "name": "fn_010a0", "module": "MOD_D", "scope": "in", "named": False, "c": "none", "done": False, "src": ""},
        {"addr": 0x10c0, "name": "clib_printf", "module": "clib", "scope": "out", "named": True, "c": "none", "done": False, "src": ""},
    ]


class _FakeHeatmapLoader:
    def __init__(self, rows):
        self._rows_cache = list(rows)

    def load_rows(self, force=False):
        return list(self._rows_cache)


def test_heatmap_classification_legend_and_modules():
    rows = _sample_fn_rows()
    assert tui.classify_heatmap_cell(rows[0])[0:2] == ("t3", "█")
    assert tui.classify_heatmap_cell(rows[1])[0:2] == ("t4", "■")
    assert tui.classify_heatmap_cell(rows[2])[0:2] == ("ref", "▓")
    assert tui.classify_heatmap_cell(rows[3])[0:2] == ("named", "▒")
    assert tui.classify_heatmap_cell(rows[4])[0:2] == ("untouched", "░")
    assert tui.classify_heatmap_cell(rows[6])[0:2] == ("oos", "·")
    # Active and failed overlays override underlying status
    assert tui.classify_heatmap_cell(rows[4], active_addrs={0x1080})[0:2] == ("active", "◆")
    assert tui.classify_heatmap_cell(rows[5], failed_addrs={0x10a0})[0:2] == ("failed", "✕")

    fn_cells = []
    for r in rows:
        k, g, col, lbl = tui.classify_heatmap_cell(r, active_addrs={0x1080}, failed_addrs={0x10a0})
        fn_cells.append(dict(r, key=k, glyph=g, color=col, tier=lbl))
    mod_cells = tui.build_module_cells(fn_cells, active_modules={"MOD_C"}, failed_modules={"MOD_D"})
    by_m = {m["module"]: m for m in mod_cells}
    assert by_m["MOD_A"]["glyph"] == "■"  # 100% done (1 T3 + 1 T4)
    assert by_m["MOD_B"]["glyph"] == "▓"  # has ref
    assert by_m["MOD_C"]["glyph"] == "◆"  # active
    assert by_m["MOD_D"]["glyph"] == "✕"  # failed
    assert "clib" not in by_m

    insp_fn = tui.format_inspector(fn_cells[0], "functions")
    assert "0x1000" in insp_fn and "FooT3" in insp_fn and "MOD_A" in insp_fn and "src/a/foo.c" in insp_fn
    insp_mod = tui.format_inspector(by_m["MOD_A"], "modules")
    assert "MOD_A" in insp_mod and "2/2" in insp_mod


def test_stream_filtering_and_presets():
    assert tui.filter_stream_event({"kind": "think", "text": "x"}, "all")
    assert tui.filter_stream_event({"kind": "think", "text": "x"}, "thinking")
    assert not tui.filter_stream_event({"kind": "verify", "text": "x"}, "thinking")
    assert tui.filter_stream_event({"kind": "match", "text": "x"}, "verify")
    assert tui.filter_stream_event({"kind": "commit", "text": "x"}, "verify")
    assert not tui.filter_stream_event({"kind": "think", "text": "x"}, "verify")

    for k in ("overnight_full", "safe_80", "daytime_sprint", "wave3_unnamed"):
        cfg = tui.preset_config(k)
        args = overnight.build_cli_args(cfg)
        assert "--headless" in args
        parsed = overnight._build_parser().parse_args(args)
        assert 0.0 < parsed.window_budget <= 1.0


def test_dashboard_pilot_interactions_and_controls(tmp_path):
    root = str(tmp_path)
    # Seed live state, rate limits, and worker stream
    now = time.time()
    state = {
        "schema_version": 2,
        "pid": os.getpid(),  # alive process so runner shows active
        "run_id": "test_run_1",
        "started_at": now - 120,
        "updated_at": now,
        "status": "THINKING",
        "status_detail": "c-only MOD_C (mod_c_c)",
        "build_status": "IDENTICAL",
        "pause_requested": False,
        "stop_requested": False,
        "config": tui.preset_config("overnight_full"),
        "progress": {"start_done": 640, "done": 642, "total": 1010, "start_t3": 340, "t3": 341, "start_t4": 300, "t4": 301, "delta_done": 2},
        "metrics": {"spend_5h": 4.2, "calls_5h": 15, "spend_7d": 12.0, "calls_7d": 40,
                    "cache_hit_pct": 88.5, "sparkline": [0.1] * 24, "burn_rate_usd_per_h": 1.2,
                    "cost_per_fn": 0.06, "est_fns_left": 200, "run_cost": 0.12},
        "active_workers": [{
            "id": "mod_c_c", "provider": "claude", "module": "MOD_C", "mode": "c-only",
            "area": "mod_c_c", "stage": "draft_b0", "phase": "THINKING",
            "count": 1, "addrs": [0x1080], "started_at": now - 10, "cost": 0.03,
        }],
        "completed": [{
            "id": "mod_a_c", "provider": "claude", "time": "05:10:00", "module": "MOD_A",
            "mode": "c-only", "area": "mod_a_c", "status": "COMMITTED", "delta": 2,
            "cost": 0.12, "commit": "abc1234", "note": "abc1234", "addrs": [0x1000, 0x1020],
        }],
        "commits": [{
            "rev": "abc1234", "module": "MOD_A", "area": "mod_a_c", "delta": 2,
            "cost": 0.12, "time": "05:10:00", "message": "T3/T4: MOD_A +2 done",
        }],
        "failed_modules": ["MOD_D"],
        "failed_addrs": [0x10a0],
        "queue": [{"module": "MOD_B", "mode": "c-only", "area": "mod_b_c", "count": 2, "module_total": 2, "avg_insns": 15.0}],
    }
    live.write_json_atomic(live.state_path(root=root), state)
    live.save_rate_limits({
        "updated_at": now, "status": "allowed",
        "five_hour": {"utilization": 0.42, "used_percentage": 42.0, "resets_at": now + 3600, "status": "allowed"},
        "seven_day": {"utilization": 0.18, "used_percentage": 18.0, "resets_at": now + 86400, "status": "allowed"},
    }, root=root)
    live.append_event("mod_c_c", "think", "analyzing Watcom register allocation", root=root)
    live.append_event("mod_c_c", "match", "[T3 MATCH local] Foo@0x1080", root=root)

    async def _run():
        app = tui.WC1DashboardApp(
            live_root=root,
            heatmap_loader=_FakeHeatmapLoader(_sample_fn_rows()),
        )
        async with app.run_test(size=(120, 36)) as pilot:
            await pilot.pause(0.35)
            hm = app.query_one("#heatmap-grid", tui.HeatmapWidget)
            assert hm.mode == "functions"
            assert len(hm.cells) == 6  # OOS hidden by default

            # Toggle out-of-scope (o) and Functions <-> Modules (m)
            await pilot.press("o")
            assert len(hm.cells) == 7
            await pilot.press("m")
            assert hm.mode == "modules"
            assert len(hm.cells) == 4
            await pilot.press("m")
            assert hm.mode == "functions"

            # Stream filters a / t / v / f
            assert app._selected_worker == "mod_c_c"
            await pilot.press("t")
            assert app._stream_filter == "thinking"
            await pilot.press("v")
            assert app._stream_filter == "verify"
            await pilot.press("a")
            assert app._stream_filter == "all"
            await pilot.press("f")
            assert app._stream_follow is True

            # Pause, wake, graceful stop send IPC controls
            await pilot.press("p")
            assert live.consume_control(root=root)["action"] == "pause"
            await pilot.press("w")
            assert live.consume_control(root=root)["action"] == "wake"
            await pilot.press("x")
            assert live.consume_control(root=root)["action"] == "graceful_stop"

            # Shift+K opens confirmation modal; Esc cancels WITHOUT sending kill
            await pilot.press("K")
            assert isinstance(app.screen, tui.KillConfirmScreen)
            await pilot.press("escape")
            assert live.peek_control(root=root) is None

            # Shift+K then 'y' sends immediate kill
            await pilot.press("K")
            assert isinstance(app.screen, tui.KillConfirmScreen)
            await pilot.press("y")
            assert live.consume_control(root=root)["action"] == "kill"

            # Commits modal (g)
            await pilot.press("g")
            assert isinstance(app.screen, tui.CommitsScreen)
            await pilot.press("escape")

            # Detach (q) exits cleanly without touching background PID
            await pilot.press("q")

    asyncio.run(_run())


def test_launcher_modal_presets_and_detach_leaves_runner_alive(tmp_path):
    root = str(tmp_path)
    # Start a harmless detached background sleeper mimicking a runner
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        start_new_session=True,
    )
    try:
        live.write_json_atomic(live.state_path(root=root), {
            "pid": proc.pid, "status": "RUNNING", "run_id": "bg1",
            "progress": {"start_done": 1, "done": 1, "total": 10, "start_t3": 1, "t3": 1, "start_t4": 0, "t4": 0, "delta_done": 0},
        })

        async def _run():
            app = tui.WC1DashboardApp(
                live_root=root,
                open_launcher=True,
                heatmap_loader=_FakeHeatmapLoader(_sample_fn_rows()),
            )
            async with app.run_test(size=(120, 38)) as pilot:
                await pilot.pause(0.2)
                assert isinstance(app.screen, tui.LauncherScreen)
                # Click Daytime Sprint preset and verify inputs updated
                await pilot.click("#preset-daytime_sprint")
                await pilot.pause(0.1)
                cfg = app.screen._collect_config()
                assert cfg["max_modules"] == 5
                assert cfg["sleep_on_limit"] is False
                # Attach only -> back to dashboard -> detach with q
                await pilot.click("#btn-launch-attach")
                await pilot.pause(0.1)
                assert not isinstance(app.screen, tui.LauncherScreen)
                await pilot.press("q")

        asyncio.run(_run())
        # Runner MUST still be alive after TUI detached!
        assert live.pid_alive(proc.pid)
    finally:
        live.terminate_process_tree(proc)


def test_dashboard_worker_selection_follow_pause_and_runner_restart(tmp_path):
    """Verify switching workers in Agents & Queue, manual scroll disabling follow,
    and surviving runner restart (new run_id) seamlessly."""
    root = str(tmp_path)
    now = time.time()
    live.append_event("w_active", "think", "active thinking line", root=root)
    live.append_event("w_done", "commit", "[deadbee] committed old module", root=root)
    base_state = {
        "schema_version": 2,
        "pid": os.getpid(),
        "run_id": "run_v1",
        "started_at": now - 60,
        "updated_at": now,
        "status": "THINKING",
        "build_status": "IDENTICAL",
        "progress": {"start_done": 640, "done": 642, "total": 1010, "start_t3": 340, "t3": 341, "start_t4": 300, "t4": 301, "delta_done": 2},
        "metrics": {"spend_5h": 2.0, "calls_5h": 5, "spend_7d": 5.0, "calls_7d": 12,
                    "cache_hit_pct": 80.0, "sparkline": [0.05] * 24, "burn_rate_usd_per_h": 1.0,
                    "cost_per_fn": 0.05, "est_fns_left": 100, "run_cost": 0.1},
        "active_workers": [
            {"id": "w_active", "provider": "codex", "module": "MOD_C", "mode": "full",
             "area": "w_active", "stage": "draft", "phase": "THINKING", "count": 1, "addrs": [0x1080]},
        ],
        "completed": [
            {"id": "w_done", "provider": "claude", "time": "05:00:00", "module": "MOD_A",
             "mode": "c-only", "area": "w_done", "status": "COMMITTED", "delta": 2, "cost": 0.1, "commit": "deadbee"},
        ],
        "commits": [],
        "failed_modules": [],
        "failed_addrs": [],
        "queue": [],
    }
    live.write_json_atomic(live.state_path(root=root), base_state)

    async def _run():
        app = tui.WC1DashboardApp(
            live_root=root,
            heatmap_loader=_FakeHeatmapLoader(_sample_fn_rows()),
        )
        async with app.run_test(size=(120, 36)) as pilot:
            await pilot.pause(0.4)
            assert app._selected_worker == "w_active"

            # Focus workers table and move down to w_done
            tbl = app.query_one("#workers-table")
            tbl.focus()
            await pilot.press("down")
            await pilot.pause(0.25)
            assert app._selected_worker == "w_done"
            assert app._user_pinned_worker is True

            # Manual scroll up disables follow; 'f' re-enables follow
            stream = app.query_one("#stream-log")
            stream.focus()
            await pilot.press("pageup")
            await pilot.pause(0.1)
            assert app._stream_follow is False
            await pilot.press("f")
            assert app._stream_follow is True

            # Heatmap keyboard arrow navigation updates inspector
            hm = app.query_one("#heatmap-grid", tui.HeatmapWidget)
            hm.focus()
            assert hm.cursor_idx == 0
            await pilot.press("right")
            assert hm.cursor_idx == 1

            # Simulate runner restart with new run_id & new active worker
            live.append_event("w_new", "think", "restarted runner line", root=root)
            st2 = dict(base_state, run_id="run_v2", active_workers=[
                {"id": "w_new", "provider": "claude", "module": "MOD_B", "mode": "c-only",
                 "area": "w_new", "stage": "draft", "phase": "RUNNING", "count": 2, "addrs": [0x1040]},
            ])
            live.write_json_atomic(live.state_path(root=root), st2)
            await pilot.pause(0.5)
            assert app._last_run_id == "run_v2"
            assert app._selected_worker == "w_new"

            await pilot.press("q")

    asyncio.run(_run())


def test_real_heatmap_loader_smoke():
    if not os.path.exists(tui.path("original", "install", "war.exe")):
        pytest.skip("needs original/install/war.exe")
    loader = tui.HeatmapDataLoader()
    rows = loader.load_rows()
    in_scope = [r for r in rows if r["scope"] == "in"]
    assert len(in_scope) == 1010
    # Second call uses mtime cache
    rows2 = loader.load_rows()
    assert rows2 is rows
