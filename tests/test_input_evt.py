"""Input subsystem area tests: the event queue, keyboard ISR and DPMI hooks in
gfx_evt_vid (0x30ea0..0x31784).  Evidence: analysis/symbols/input.toml, prose
docs/subsystems/input.md.

1. Every C file the symbol database builds (`src =` in
   analysis/symbols/input.toml) still reproduces the original bytes,
   relocation targets and module-local data (T3, `wc1.match`).
2. T4: the reference C for EvtPost (0x30eb8) and EvtGet (0x31598) runs
   against the original under `wc1.cemu` on identical inputs - `cemu.load`
   compiles the file with its codegen-flags and relocates it against the
   symbol database, `run_pair` runs both sides and compares the return
   register and the watched memory (the ring, the event, the counters).
3. Structural checks: the 12-byte event record and the ISR state block that
   EvtInit clears and DPMI-locks, and the marker arithmetic of the code lock.
"""
import os
import struct

import pytest

from wc1 import cemu, match, path, symbols

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "input")

# --------------------------------------------------------------- addresses
EVT_KEY = 0x5A880           # keyboard template (KeyboardISR)
EVT_MOVE = 0x5A88C          # move template, type 1 / sub 3
EVT_BUTTON = 0x5A898        # MouseButtonEvent's template
EVT_IDLE = 0x5A8A4          # idle template, type 0x400 / sub 8
MOUSE_RAW_X = 0x5A8B0
MOUSE_RAW_Y = 0x5A8B2
EVT_MASK = 0x5A8B4
EVT_MOVE_PENDING = 0x5A8BA  # Event *
EVT_QUEUE = 0x5A8BE         # Event *
EVT_TAIL = 0x5A8C2
EVT_HEAD = 0x5A8C4
EVT_QUEUE_SIZE = 0x5A8C6
EVT_COUNT = 0x5A8C8
MOUSE_X = 0x5A8CA
MOUSE_Y = 0x5A8CC
EVT_LAST_IDLE = 0x55434
SCANCODE_SOURCE = 0x553B4
SCANCODE_TABLE = 0x5A9DF
KBD_E0 = 0x5A9D5
KBD_E1 = 0x5A9D7
KBD_PAUSE = 0x5A9BE
OLD_INT9 = 0x5A9D9
KEY_DOWN_TABLE = 0x5A8D4

EVT_POST = 0x30EB8
EVT_GET = 0x31598
DISABLE = 0x349B8
ENABLE = 0x349BA
CLOCK = 0x30E98

EVENT_SIZE = 12


# ------------------------------------------------------------------ helpers
# The T3-matched sources of this area.  The TOML entries carry
# `verified_by = "match: ..."` but deliberately no `src =`: the session owner
# wires the files into the build (`src =` changes the shared build), so the
# re-check below names the files itself.
MATCHED = [
    ("isr_region_start.c", ["IsrRegionStart_"]),
    ("isr_region_end.c", ["IsrRegionEnd_"]),
    ("mouse_button_event.c", ["MouseButtonEvent_"]),
    ("mouse_callback.c", ["MouseCallback"]),
    ("keyboard_isr.c", ["KeyboardISR"]),
    ("dpmi_lock_region.c", ["DpmiLockRegion_"]),
    ("dpmi_unlock_region.c", ["DpmiUnlockRegion_"]),
    ("evt_keyboard_vector.c", ["EvtHookKeyboard_", "EvtUnhookKeyboard_"]),
    ("evt_init_mouse.c", ["EvtInitMouse_"]),
    ("evt_shutdown_mouse.c", ["EvtShutdownMouse_"]),
    ("evt_pump.c", ["EvtPump_"]),
    ("evt_init.c", ["EvtInit_"]),
    ("evt_shutdown.c", ["EvtShutdown_"]),
]


@pytest.fixture(scope="module")
def prog():
    from wc1 import codegen_sweep
    return codegen_sweep.program()


@pytest.mark.parametrize("name,funcs_expected", MATCHED,
                         ids=[m[0] for m in MATCHED])
def test_matched_c(name, funcs_expected, prog):
    """The area's T3 sources still reproduce the original bytes, relocation
    targets and module-local data (wc1.match)."""
    src = os.path.join(AREA, name)
    out = path("build", "input", "t3_" + name + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, match.file_cflags(src), out)
    by_link = {e["link_name"]: e for t in symbols.load()[:2] for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, (src, bad)
    assert sorted(res_name for res_name in funcs_expected) == \
        sorted(r[0] for r in res if not r[0].startswith("["))


def test_every_area_function_has_an_entry():
    """All 16 discovered starts of the range are in the database and named."""
    from wc1 import analysis
    p = analysis.run()
    starts = {f["start"] for f in p.functions if 0x30EA0 <= f["start"] < 0x31784}
    funcs, _, _ = symbols.load()
    assert len(starts) == 16, [hex(a) for a in sorted(starts)]
    for a in starts:
        assert a in funcs, hex(a)
        assert not funcs[a]["name"].startswith("fn_"), hex(a)


# ---------------------------------------------------- structural (no emu)
def test_event_record_and_state_block():
    """The 12-byte record, the four templates and the ISR scratch all live in
    the 0x1df-byte block EvtInit clears (memset 0x5a880..0x5aa5e) - which is
    also the block it DPMI-locks; the keyboard vector and the scancode table
    copy sit at its end."""
    assert EVT_KEY == 0x5A880
    for tpl in (EVT_MOVE, EVT_BUTTON, EVT_IDLE):
        assert EVT_KEY < tpl < EVT_KEY + 0x1DF
    for a in (MOUSE_RAW_X, EVT_MASK, EVT_MOVE_PENDING, EVT_QUEUE, EVT_TAIL,
              EVT_HEAD, EVT_QUEUE_SIZE, EVT_COUNT, MOUSE_X, MOUSE_Y,
              KEY_DOWN_TABLE, SCANCODE_TABLE, KBD_E0, KBD_E1, KBD_PAUSE, OLD_INT9):
        assert EVT_KEY <= a < EVT_KEY + 0x1DF, hex(a)
    # the scancode fixup copy ends exactly at the block end
    assert SCANCODE_TABLE + 0x80 == EVT_KEY + 0x1DF
    # the ring stride is the record size (EvtInit allocates size*12)
    assert struct.calcsize("<5H2B") == EVENT_SIZE


def test_evt_init_locks_the_state_and_the_isr_code():
    """EvtInit passes (0x5a880, 0x1df) and (IsrRegionStart, end-start+1) to
    DpmiLockRegion - the two DPMI-locked regions the ISRs run from."""
    from wc1 import analysis
    p = analysis.run()
    img = bytes(p.image[p.code.index])
    base = p.code.base

    def at(a, n):
        return img[a - base:a - base + n]

    # memset(&evt_key, 0, 0x1df) and DpmiLockRegion(&evt_key, 0x1df)
    assert at(0x316B1, 5) == bytes([0xBB]) + struct.pack("<I", 0x1DF)
    assert at(0x31731, 5) == bytes([0xBA]) + struct.pack("<I", 0x1DF)
    # memcpy(scancode_fixup_table, 0x553b4, 0x80)
    assert at(0x3171D, 5) == bytes([0xBB]) + struct.pack("<I", 0x80)
    # DpmiLockRegion(IsrRegionStart, IsrRegionEnd - IsrRegionStart + 1)
    assert at(0x31740, 5) == bytes([0xBA]) + struct.pack("<I", 0x30EA0)
    assert at(0x31745, 5) == bytes([0xB8]) + struct.pack("<I", 0x312D8)
    assert at(0x3174A, 5)[:2] == b"\x29\xd0"          # sub eax,edx
    assert at(0x3174C, 3) == b"\x8d\x50\x01"          # lea edx,[eax+1]


def test_scancode_fixup_source_is_the_table_evtinit_copies():
    """0x553b4 holds the 0x80-byte table EvtInit copies to 0x5a9df: the
    extended (0xE0-prefixed) scancodes are remapped into 0x70..0x7f so that a
    key-down event carries a distinct code for e.g. keypad-enter vs Enter."""
    from wc1 import analysis
    p = analysis.run()
    d = bytes(p.image[p.data.index])
    base = p.data.base
    src = d[SCANCODE_SOURCE - base:SCANCODE_SOURCE - base + 0x80]
    assert len(src) == 0x80
    expect = {0x1C: 0x70, 0x1D: 0x71, 0x35: 0x72, 0x37: 0x73, 0x38: 0x74,
              0x47: 0x76, 0x48: 0x77, 0x49: 0x78, 0x4B: 0x79, 0x4D: 0x7A,
              0x4F: 0x7B, 0x50: 0x7C, 0x51: 0x7D, 0x52: 0x7E, 0x53: 0x7F}
    assert {i: v for i, v in enumerate(src) if v} == expect


# ------------------------------------------------------- T4: difftests
def _u16(emu, a, v):
    emu.write(a, struct.pack("<H", v & 0xFFFF))


def _u32(emu, a, v):
    emu.write(a, struct.pack("<I", v & 0xFFFFFFFF))


def _post_env(emu, size=4):
    """A ring of `size` events plus a fresh event buffer; both sides get the
    same globals (EvtPost takes only the event pointer)."""
    ring = emu.alloc(EVENT_SIZE * size)
    ev = emu.alloc(EVENT_SIZE)
    emu.write(ring, b"\x00" * (EVENT_SIZE * size))
    _u32(emu, EVT_QUEUE, ring)
    _u16(emu, EVT_QUEUE_SIZE, size)
    emu.stubs[DISABLE] = lambda e: 0
    emu.stubs[ENABLE] = lambda e: 0
    return ring, ev


def test_t4_isr_region_markers():
    """0x30ea0/0x312d8: the two empty DPMI-lock markers (T3 since 2026-11-18,
    the difftest is kept as the behavioural check).  They have no effect:
    same final stack, no memory writes."""
    from wc1.emu import Emu
    emu = Emu()
    cm = cemu.load(emu, os.path.join(AREA, "isr_region_start.c"))
    assert cemu.run_pair(emu, 0x30EA0, cm, "IsrRegionStart_", out_regs=()) == []
    cm2 = cemu.load(emu, os.path.join(AREA, "isr_region_end.c"))
    assert cemu.run_pair(emu, 0x312D8, cm2, "IsrRegionEnd_", out_regs=()) == []


def test_t4_evt_post():
    """0x30eb8 EvtPost: null event, masked-out types, full ring, the
    stamping of the mouse position, the ring copy and the head wrap."""
    from wc1.emu import Emu
    emu = Emu()
    cm = cemu.load(emu, os.path.join(AREA, "evt_post_reference.c"))
    ring, ev = _post_env(emu)
    watch = [(EVT_COUNT, 2), (EVT_HEAD, 2), (ring, EVENT_SIZE * 4), (ev, EVENT_SIZE)]
    cases = [
        # type, mask, count, head, x, y, null?
        (0x080, 0x380, 0, 0, 10, 20, False),
        (0x100, 0x380, 3, 3, 160, 100, False),      # wrap: 3 -> 0
        (0x002, 0x001, 0, 0, 1, 2, False),          # masked out
        (0x080, 0x380, 4, 0, 5, 6, False),          # ring full
        (0x001, 0x001, 2, 1, 319, 199, False),
        (0x400, 0xFFFF, 0, 0, 0, 0, False),
        (0x080, 0x380, 1, 2, 7, 8, True),           # null pointer
    ]
    for typ, mask, count, head, x, y, is_null in cases:
        _u16(emu, EVT_MASK, mask)
        _u16(emu, EVT_COUNT, count)
        _u16(emu, EVT_HEAD, head)
        _u16(emu, MOUSE_X, x)
        _u16(emu, MOUSE_Y, y)
        emu.write(ring, b"\x00" * (EVENT_SIZE * 4))
        emu.write(ev, struct.pack("<2H2H2B H", typ, 9, 0, 0, 0x55, 0, 0))
        diffs = cemu.run_pair(emu, EVT_POST, cm, "EvtPost_", 0 if is_null else ev,
                              watch=watch, out_regs=("eax",))
        assert diffs == [], (hex(typ), hex(mask), count, head, diffs)


def test_t4_evt_get():
    """0x31598 EvtGet: ring events (with tail wrap), the coalesced move
    event, the 5-tick idle gate and the empty result."""
    from wc1.emu import Emu
    emu = Emu()
    cm = cemu.load(emu, os.path.join(AREA, "evt_get_reference.c"))
    ring, out = _post_env(emu)
    emu.stubs[DISABLE] = lambda e: 0
    emu.stubs[ENABLE] = lambda e: 0
    now = [100]
    emu.stubs[CLOCK] = lambda e: now[0]
    # the move/idle templates as EvtInit leaves them
    _u16(emu, EVT_MOVE + 0, 1)
    _u16(emu, EVT_MOVE + 2, 3)
    _u16(emu, EVT_IDLE + 0, 0x400)
    _u16(emu, EVT_IDLE + 2, 8)
    watch = [(out, EVENT_SIZE), (EVT_COUNT, 2), (EVT_TAIL, 2),
             (EVT_MOVE_PENDING, 4), (EVT_LAST_IDLE, 4), (ring, EVENT_SIZE * 4)]
    cases = [
        # count, tail, now, last_idle, move_pending, mx, my
        (0, 0, 100, 95, 0, 10, 20),      # idle gate opens (100-95 >= 5)
        (0, 0, 100, 96, 0, 10, 20),      # gate closed
        (0, 0, 100, 96, 1, 10, 20),      # pending move event first
        (1, 0, 100, 100, 0, 11, 22),     # one queued event
        (2, 3, 100, 100, 0, 12, 23),     # tail wraps 3 -> 0
        (3, 2, 104, 100, 0, 13, 24),     # queued events win over the gate
    ]
    for count, tail, clock_now, last_idle, pending, mx, my in cases:
        now[0] = clock_now
        _u16(emu, EVT_COUNT, count)
        _u16(emu, EVT_TAIL, tail)
        _u32(emu, EVT_LAST_IDLE, last_idle)
        _u32(emu, EVT_MOVE_PENDING, EVT_MOVE if pending else 0)
        _u16(emu, MOUSE_X, mx)
        _u16(emu, MOUSE_Y, my)
        for i in range(4):
            emu.write(ring + i * EVENT_SIZE,
                      struct.pack("<4H2B H", 0x80 + i, i, mx, my, 0x1C + i, 0, 0))
        emu.write(out, b"\x00" * EVENT_SIZE)
        diffs = cemu.run_pair(emu, EVT_GET, cm, "EvtGet_", out,
                              watch=watch, out_regs=("eax",))
        assert diffs == [], (count, tail, clock_now, last_idle, pending, diffs)
