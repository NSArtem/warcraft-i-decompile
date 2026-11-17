"""wc1.cemu: the T4 harness (compiled C under wc1.emu, docs/GOAL.md M1).

A compiled C module is placed in the emulator next to the original image:
external relocations resolve to the symbol-database addresses (so the C
touches the same globals and calls the same functions as the original) and
module-local segments (string literals, statics) are copied into the
emulator's scratch area.  The C functions are then called like the original
ones, and `run_pair` runs both on identical inputs and compares the results.
"""
import os
import struct

import pytest

from wc1 import cemu, path

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM (nix develop)")

SCORE_REF = path("src", "save_score", "score_reference.c")
# the reference C declares the game-state dword at 0x59614; the DB names the
# word inside it (game_mode 0x59616), so the harness gets it as an extra
SCORE_EXTRA = {"_game_state": 0x59614}
MEN = 0x58E28


def test_module_loads_and_functions_are_addressable():
    from wc1.emu import Emu
    emu = Emu()
    cm = cemu.load(emu, SCORE_REF, extra=SCORE_EXTRA)
    assert cm.fn("TotalActiveMen_") in cm.publics.values()
    assert cm.fn("ScoreSetPage_") > cm.fn("TotalActiveMen_")
    with pytest.raises(cemu.CEmuError):
        cm.fn("NoSuchFunction_")


def test_compiled_c_matches_the_original_on_shared_data():
    """TotalActiveMen (0x24e50): the reference C sums the original's own
    player_active_men array and returns the same value."""
    from wc1.emu import Emu
    emu = Emu()
    cm = cemu.load(emu, SCORE_REF, extra=SCORE_EXTRA)
    for vals in ([0, 0, 0, 0], [1, 2, 3, 4], [0xFFFF] * 4, [0x1234, 0, 0x4321, 0x8000]):
        emu.write(MEN, struct.pack("<4H", *vals))
        diffs = cemu.run_pair(emu, 0x24E50, cm, "TotalActiveMen_", watch=[(MEN, 8)])
        assert diffs == [], diffs


def test_local_segments_and_internal_calls(tmp_path):
    """A module-local const array and an internal (static) call must be
    relocated into the emulator's copy, not the original image."""
    from wc1.emu import Emu
    src = tmp_path / "cemu_probe.c"
    src.write_text(
        '/* codegen-flags: -s -ot -ol -4r -zp2 */\n'
        'extern unsigned short player_active_men[4];\n'
        'static const char msg[] = "cemu-probe";\n'
        'static int twice(int v) { return v + v; }\n'
        'const char *CemuProbeString(void) { return msg; }\n'
        'unsigned CemuProbeTwice(unsigned v) { return twice(v) + player_active_men[0]; }\n')
    emu = Emu()
    cm = cemu.load(emu, str(src))
    p = cm.call("CemuProbeString_")
    assert emu.cstr(p) == b"cemu-probe"
    assert p != 0 and p not in range(0x10000, 0x800000), "local data must not alias the image"
    emu.write(MEN, struct.pack("<4H", 7, 0, 0, 0))
    assert cm.call("CemuProbeTwice_", 5) == 17
    emu.write(MEN, struct.pack("<4H", 100, 0, 0, 0))
    assert cm.call("CemuProbeTwice_", 21) == 142


def test_unknown_external_symbol_is_reported(tmp_path):
    src = tmp_path / "cemu_bad.c"
    src.write_text('extern int no_such_symbol_xyz;\nint CemuBad(void) { return no_such_symbol_xyz; }\n')
    from wc1.emu import Emu
    with pytest.raises(cemu.CEmuError) as ex:
        cemu.load(Emu(), str(src))
    assert "no_such_symbol_xyz" in str(ex.value)


def test_run_pair_reports_differences():
    """run_pair must notice a wrong model: feed the C a different argument
    than the original (a deliberate mismatch) and require a report."""
    from wc1.emu import Emu
    emu = Emu()
    cm = cemu.load(emu, SCORE_REF, extra=SCORE_EXTRA)
    emu.write(0x5A0D4, struct.pack("<H", 0))
    # ScoreSetPage(page) stores the page in score_page (0x5a0d4)
    assert cemu.run_pair(emu, 0x257F8, cm, "ScoreSetPage_", 5, out_regs=(),
                         watch=[(0x5A0D4, 2)]) == []
    real_call = cm.call
    cm.call = lambda name, *a, **k: real_call(name, 0, **k)   # wrong input
    diffs = cemu.run_pair(emu, 0x257F8, cm, "ScoreSetPage_", 5, out_regs=(),
                          watch=[(0x5A0D4, 2)])
    assert diffs and "memory 0x5a0d4" in diffs[0], diffs
    cm.call = real_call
