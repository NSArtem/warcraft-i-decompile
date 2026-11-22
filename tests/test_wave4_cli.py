"""Wave 4 wiring: TUI wave selector and the batch_driver t3-recovery subcommand (fakes only)."""
import asyncio
import os
import types

import pytest

from wc1 import batch_driver, overnight, t3_audit, tui, wave4


class _Rows:
    def __init__(self):
        self._rows_cache = []

    def load_rows(self, force=False):
        return []


def test_tui_launcher_offers_wave4_and_forwards_it(tmp_path):
    from textual.widgets import Select

    async def _run():
        app = tui.WC1DashboardApp(live_root=str(tmp_path), open_launcher=True, heatmap_loader=_Rows())
        async with app.run_test(size=(120, 38)) as pilot:
            await pilot.pause(0.2)
            assert isinstance(app.screen, tui.LauncherScreen)
            sel = app.screen.query_one("#sel-wave", Select)
            sel.value = "wave4"
            await pilot.pause(0.1)
            cfg = app.screen._collect_config()
            assert cfg["wave"] == "wave4"
            args = overnight.build_cli_args(cfg)
            parsed = overnight._build_parser().parse_args(args)
            assert parsed.wave == "wave4" and parsed.wave4_max_calls == 2
            sel.value = "all"
            await pilot.pause(0.1)
            assert app.screen._collect_config()["wave"] == "all"
            await pilot.press("q")
    asyncio.run(_run())


def test_tui_presets_still_valid_for_all_waves():
    for w in ("all", "wave2", "wave3", "wave4"):
        cfg = dict(tui.preset_config("safe_80"), wave=w)
        assert overnight._build_parser().parse_args(overnight.build_cli_args(cfg)).wave == w


# batch_driver t3-recovery -----------------------------------------------------------------------
def cand(addr):
    return {"addr": addr, "addr_hex": f"{addr:#x}", "name": "F", "ref": "src/x.c", "module": "m", "group": 2}


@pytest.fixture
def driver(tmp_path, monkeypatch):
    monkeypatch.setattr(batch_driver, "path", lambda *p: os.path.join(str(tmp_path), *p))
    monkeypatch.setattr(t3_audit, "load_inputs", lambda: (types.SimpleNamespace(), [], {}, [], []))
    monkeypatch.setattr(t3_audit, "Ctx", lambda p, f, b, objdir: types.SimpleNamespace(objdir=objdir))
    seen = {}
    monkeypatch.setattr(wave4, "discover", lambda inputs=None, **kw: ([cand(0x10), cand(0x20)], {}))

    def rec(c, sib, ctx, llm=None, max_calls=2, **kw):
        seen.update(cand=c, siblings=sib, max_calls=max_calls, llm=llm)
        return {"outcome": seen.get("outcome", wave4.NO_IMPROVEMENT)}
    monkeypatch.setattr(wave4, "run_recovery", rec)
    return seen


def test_t3_recovery_runs_one_function_with_bounded_calls(driver, tmp_path):
    rc = batch_driver.main(["t3-recovery", "0x10", "--area", "w4_10", "--max-calls", "1"])
    assert rc == 0
    assert driver["cand"]["addr"] == 0x10 and driver["max_calls"] == 1
    assert [s["addr"] for s in driver["siblings"]] == [0x10, 0x20]
    assert not (tmp_path / "build" / "wave4" / "obj" / "10").exists()       # scratch objdir cleaned
    assert (tmp_path / "build" / "driver" / "w4_10_sys.txt").read_text() == wave4.REPAIR_RULES


def test_t3_recovery_ineligible_address_is_nothing_to_do(driver):
    assert batch_driver.main(["t3-recovery", "0x99"]) == batch_driver.EXIT_NOTHING_TO_DO
    assert "cand" not in driver


def test_t3_recovery_toolchain_outcome_exits_78(driver):
    driver["outcome"] = wave4.TOOLCHAIN_ERROR
    assert batch_driver.main(["t3-recovery", "0x10"]) == batch_driver.EXIT_TOOLCHAIN


def test_t3_recovery_llm_goes_through_the_ledger_call(driver, monkeypatch):
    calls = []
    monkeypatch.setattr(batch_driver, "_call_llm", lambda prompt, schema, sysf, **kw: (
        calls.append(kw) or ({"patches": []}, 0.0, {})))
    batch_driver.main(["t3-recovery", "0x10", "--max-cost", "0.5"])
    assert driver["llm"]("p", {}, "lbl") == {"patches": []}
    assert calls[0]["stage"] == "stage4" and calls[0]["max_cost"] == 0.5 and calls[0]["label"] == "lbl"
