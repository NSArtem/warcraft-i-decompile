"""Input subsystem area tests: the event queue, ISR markers and DPMI hooks in
gfx_evt_vid (0x30ea0..0x31789).  Evidence: analysis/symbols/input.toml, prose
docs/subsystems/input.md.

T3 re-checks (wc1.match) and T4 difftests (wc1.cemu.run_pair) as named by
`src =` / `ref_verified_by` in the symbol database.
"""
import os

import pytest

from wc1 import cemu, match, path, symbols

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

ISR_START, ISR_END = 0x30EA0, 0x312D8


def test_t4_isr_region_markers():
    """0x30ea0/0x312d8: the two empty DPMI-lock markers.  They differ from
    OW2 only in the OD frame reservation (`sub esp,4` vs `sub esp,0`), which
    leaves no observable effect: same final stack, no memory writes."""
    from wc1.emu import Emu
    emu = Emu()
    cm = cemu.load(emu, path("src", "input", "isr_region_start.c"))
    diffs = cemu.run_pair(emu, ISR_START, cm, "IsrRegionStart_", out_regs=())
    assert diffs == [], diffs
    cm2 = cemu.load(emu, path("src", "input", "isr_region_end.c"))
    diffs = cemu.run_pair(emu, ISR_END, cm2, "IsrRegionEnd_", out_regs=())
    assert diffs == [], diffs
