"""Game logic area 0x2c4e0..0x2efd0 (docs/subsystems/game_2c4e0.md).

1. Every C file with `src =` in the symbol database (analysis/symbols/
   game_2c4e0.toml) still reproduces the original bytes, relocation targets
   and module-local data (T3, wc1.match).
2. The reference files (draw-list sort/insert, the one-argument order setter,
   PathPeekStep) are known near misses. If one starts matching, it must be
   promoted to the built file.
"""
import os

import pytest

from wc1 import codegen_sweep, match, path, symbols

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "game_2c4e0")
MATCHED = ["draw_list_remove.c", "unit_reset_path.c", "unit_damage_frame.c", "unit_orders.c"]
REFERENCE = ["draw_list_reference.c", "unit_orders_reference.c", "path_reference.c"]


@pytest.fixture(scope="module")
def prog():
    return codegen_sweep.program()


def _flags(src):
    """Full wcc flags, and the codegen-flags tail that codegen_sweep prepends BASE_CFLAGS to."""
    full = match.file_cflags(src)
    prefix = match.BASE_CFLAGS + " "
    assert full.startswith(prefix), full
    return full, full[len(prefix):]


@pytest.mark.parametrize("name", MATCHED)
def test_matched_c(name, prog):
    src = os.path.join(AREA, name)
    out = path("build", "game_2c4e0", "t3_" + name + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    full, _ = _flags(src)
    mod = match.compile_c(src, full, out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, bad


@pytest.mark.parametrize("name", REFERENCE)
def test_reference_is_still_a_near_miss(name):
    src = os.path.join(AREA, name)
    _, codegen = _flags(src)
    _, rows, err = codegen_sweep.sweep(src, [codegen], quiet=True)[0]
    assert rows is not None, err
    assert rows
    for fn, addr, status, _, _ in rows:
        assert status != "MATCH", f"{fn} {addr:#x} now matches: promote it to the built file"
