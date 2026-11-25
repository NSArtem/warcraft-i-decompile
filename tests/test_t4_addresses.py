"""The T4 tests that share symbol addresses between many cases resolve them once per
test invocation: setup, watched memory and stubs follow the symbol table of that run."""
import importlib
import os
import random
import shutil

import pytest

from wc1 import path, symbols, t4spec


class FakeEmu:
    """Records what a test prepares; nothing is executed."""
    def __init__(self):
        self.written, self.top = set(), 0x70000000

    def alloc(self, size, align=1):
        self.top += 0x10000
        return self.top

    def write(self, addr, data):
        self.written.add(addr)


def prepared(monkeypatch, test):
    """Addresses written before the cases of the test run, and those it watches or stubs."""
    emu = FakeEmu()
    observed = set()

    def run_spec(src, name, orig, cases, *, watch=(), stubs=(), extra=None, init_emu=None,
                 rand_cases=0, rand_gen=None, **kw):
        if init_emu:
            init_emu(emu)
        rng = random.Random(1)
        for c in list(cases) + [rand_gen(rng) for _ in range(rand_cases)]:
            emu.written.update(c.mem)
            if c.setup:
                c.setup(emu)
        observed.update(a for a, _ in watch)
        observed.update(s.addr for s in stubs)
        observed.update((extra or {}).values())
    with monkeypatch.context() as m:
        m.setattr(t4spec, "run_spec", run_spec)
        test()
    return emu.written, observed


# test, symbols its setup writes, symbols it watches or stubs
TESTS = [
    ("test_mod_1e9a0.test_fog_update_tile", ["_fog_map", "_terrain_scan_table"], []),
    ("test_mod_25ba0_c.test_selection_next", ["_selected_units", "_selection_index", "_net_event_pending"],
     ["_selected_units", "_selection_index", "_net_event_pending"]),
    ("test_mod_34c70_c.test_palette_lerp", ["_palette_base", "_palette_target", "_palette_cur"],
     ["_palette_cur", "_VgaSetPaletteRange"]),
    ("test_mod_349f0_c.test_dirty_rect_add_layer", ["_dat_5aa92", "_dirty_x1", "_dirty_y2"],
     ["_dat_5aa92", "_dirty_x1", "_dirty_y2", "_dirty_w"]),
    ("test_score.test_score_update", ["_score_page", "_score_page_shown", "_dirty_x1"],
     ["_score_page_shown", "_dirty_x1", "ScreenUpdate_"]),
    ("test_score.test_score_init", ["_scenario_number", "_score_page", "_score_cap_tbl"],
     ["_score_page", "_score_cap", "LayerAdd_", "BitmapCloneAlloc_"]),
]


@pytest.fixture
def db(tmp_path, monkeypatch):
    """A private copy of the symbol database (the effective root of the loaders)."""
    d = tmp_path / "analysis" / "symbols"
    shutil.copytree(path("analysis", "symbols"), d)
    for mod in (symbols, t4spec):
        monkeypatch.setattr(mod, "path", lambda *p: os.path.join(str(tmp_path), *p))
    return d


def current():
    """link name -> address, as the tests resolve it."""
    return {n: e["addr"] for n, e in t4spec.by_link_lenient().items()}


@pytest.mark.parametrize("test, written, observed", TESTS, ids=[t[0] for t in TESTS])
def test_every_invocation_uses_the_current_symbol_table(db, monkeypatch, test, written, observed):
    mod, func = test.split(".")
    mod = importlib.import_module(mod)
    func = getattr(mod, func)
    start = current()
    # _dat_5aa92 is not in the database: the test falls back to its own TBL
    before = {n: start[n] if n != "_dat_5aa92" else mod.TBL for n in written + observed}
    w0, o0 = prepared(monkeypatch, func)
    assert {before[n] for n in written} <= w0 and {before[n] for n in observed} <= o0

    # move each symbol, one edit and one rerun at a time, in the same process
    # (of two entries with one link name the one found last wins: data, later files)
    for k, (n, old) in enumerate(before.items()):
        new = 0x60000000 + 0x1000 * k
        kind, name = ("data", n[1:]) if n.startswith("_") else ("func", n[:-1])
        with open(db / "zz_moved.toml", "a") as fh:
            fh.write(f'[[{kind}]]\naddr = {new:#x}\nname = "{name}"\n')
        assert current()[n] == new
        w, o = prepared(monkeypatch, func)
        assert (new in w, old in w) == (n in written, False), n
        assert (new in o, old in o) == (n in observed, False), n

    (db / "zz_moved.toml").unlink()             # nothing of the edits is left
    assert prepared(monkeypatch, func) == (w0, o0)
    # another root, without any symbol: never the addresses of the previous one
    for f in db.iterdir():
        f.unlink()
    try:
        w, o = prepared(monkeypatch, func)
    except KeyError:
        return
    assert not {before[n] for n in start.keys() & before} & (w | o)
