"""Tests for the mod_2efd0 area (0x2efd0..0x3024e): the map selection layer
and the mission-end (victory/defeat) conditions plus the win/lose screen.

1. T3 re-checks: every C file the symbol database builds (`src =` in
   analysis/symbols/mod_2efd0.toml) still reproduces the original bytes,
   relocation targets and module-local data (`wc1.match`).
2. T4: the reference C of the functions that do not match runs against the
   original under `wc1.cemu` on identical inputs - the callees with side
   effects are stubbed (their arguments are recorded where the sequence
   matters), `run_pair` compares the return register and the watched memory.
3. Structural checks: the module boundaries, the message/number tables and
   the selection box layout documented in docs/subsystems/mod_2efd0.md.
"""
import os

import pytest

from wc1 import analysis, cemu, le, match, path, symbols
from wc1.emu import Emu

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "mod_2efd0")

# --------------------------------------------------------------- addresses
SELECTION_BOX = 0x5A7D0          # anchor x/y, min x/y, max x/y, w, h, visible
END_ACTION = 0x5A860             # void (*)(void): the mission-end action
END_DONE = 0x5A864
END_TICKS = 0x5A866
END_TIMER = 0x5A868
END_BM = 0x5A7F0                 # 184x112 panel bitmap
END_VALUES = 0x5A7F8             # 13 longs
END_TARGETS = 0x5A82C            # 13 longs
END_TEXT_BM = 0x552F8            # 290x128 numbers bitmap
VALUE_STEP = 0x5530C
VALUE_X = 0x55326
VALUE_Y = 0x55340
SCENARIO_OBJECTIVES = 0x50092
CHEAT_FLAGS = 0x51214
GAME_MODE = 0x59616
PLAYER_MEN = 0x58E28             # unsigned short[4]
PLAYER_BUILDINGS = 0x58E1E       # unsigned short[4]
PLAYER_HALLS = 0x58DF6           # unsigned short[4]
PLAYER_TOWN_HALL = 0x58DB0       # void *[5]
PLAYER_WORKERS = 0x58DD8
PLAYER_CAP = 0x58DEC
TRAINING = 0x50D84
UNIT_COUNT = 0x50D98
GOLD = 0x50074
LUMBER = 0x50060
DEAD_MEN = 0x50D8E
DEAD_BUILDINGS = 0x50DA2
HARVEST_GOLD = 0x50DC0
HARVEST_LUMBER = 0x50DD4
PLAYER_SCORE = 0x50E34
PLAYER_SELECTION_COUNT = 0x5A110
SELECTION_LOCAL = 0x5A118
MOD_ALL = 0x5A928
MOD_ADD = 0x5A940
UNIT_ARRAY = 0x59640
UNIT_SIZE = 0x5C
MAP_FLAGS = 0x5857C
TYPE_IS_CREATURE = 0x51CC0
UNIT_PIXEL_SIZE = 0x51B9C
MOVIE_STATE = 0x58DA4
END_PANEL_RECT = 0x55300
END_SOUND_IDS = 0x5535A
FULL_SCREEN_RECT = 0x514D8
MAP_VIEW_RECT = 0x51EEC
ACCESS = 0x5A7BC                 # the unit the map press/release works on

# callees (stubbed in the T4 tests)
NET_SEND_ORDER = 0x21A58
NET_SEND_CONTROL = 0x21C20
MAP_CURSOR_REFRESH = 0x1B9B8
SELECTION_FIRST = 0x25CC4
SELECTION_NEXT = 0x25C50
SELECTION_SET = 0x262A0
PLACE_BOX_ACTIVE = 0x22538
INPUT_BLOCKED = 0x2B308
SCREEN_INPUT_INIT = 0x1A328
SET_CURSOR = 0x13DD0
MOUSE_SET_RANGE = 0x33040
RECT_OUTLINE = 0x348C0
DRAW_TEXT = 0x31DCC
TEXT_WIDTH = 0x32060
LAYER_INVALIDATE = 0x31F70
LAYER_ADD = 0x21D0C
SCREEN_UPDATE = 0x321E8
BITMAP_CLEAR = 0x31FC0
BITMAP_BLIT = 0x32410
BITMAP_BLIT_TRANSPARENT = 0x325D0
SPRINTF = 0x31BE2
STRLEN = 0x31D1A
SND_PLAY = 0x26958
SND_STOP = 0x269B8
SND_RELEASE_ALL = 0x271F4
SND_LOAD_TABLE = 0x267FC
MUSIC_START = 0x26784
MUSIC_CLEAR = 0x267E0
CURSOR_LAYER_SHOW = 0x32940
RESOURCE_BEGIN = 0x31870
RESOURCE_READ = 0x32740
RESOURCE_READ_HDR = 0x323E0
RESOURCE_FREE_BODY = 0x21CF0
FLIC_OPEN = 0x1933C
FLIC_REWIND = 0x193FC
FLIC_NEXT = 0x19450
FLIC_RESTART = 0x19420
FLIC_CLOSE = 0x193DC
UI_INPUT_INIT = 0x18488
UI_EVENT_PUMP = 0x184CC
EVT_PUMP = 0x31568
PACKET_TICK = 0x21844
RANK_NAME = 0x255B8
SCORE_TICK_INCOME = 0x24E90
TEXT_COLOR_BASE = 0x32030
PALETTE_SET = 0x33150
PALETTE_FADE_IN = 0x32E80
PALETTE_FADE_OUT = 0x32FB0
VICTORY_DIALOG = 0x1AA7C
DEFEAT_DIALOG = 0x1AB28
GDS_ALLOC = 0x32558
GDS_FREE = 0x32780
MISSION_DEFEAT = 0x2F73C

# --------------------------------------------------------------- helpers


def u16(emu, addr, off=0, value=None):
    if value is None:
        return int.from_bytes(emu.read(addr + off, 2), "little")
    emu.write(addr + off, (value & 0xFFFF).to_bytes(2, "little"))


def u32(emu, addr, off=0, value=None):
    if value is None:
        return int.from_bytes(emu.read(addr + off, 4), "little")
    emu.write(addr + off, value.to_bytes(4, "little"))


def stub(emu, addr, ret=0, log=None, name=None, pops=0):
    """Install a stub that records its name (and arguments) and returns `ret`."""
    def fn(e):
        if log is not None:
            log.append(name or f"{addr:#x}")
        return ret
    emu.stubs[addr] = fn
    if pops:
        emu.stub_pops[addr] = pops
    return fn


def stub_all(emu, log=None):
    """Neutral stubs for every callee of this object (returns 0 except where a
    non-zero result is needed to take a branch)."""
    for a in (NET_SEND_ORDER, MAP_CURSOR_REFRESH, SELECTION_SET, PLACE_BOX_ACTIVE,
              INPUT_BLOCKED, SCREEN_INPUT_INIT, SET_CURSOR, MOUSE_SET_RANGE,
              RECT_OUTLINE, DRAW_TEXT, LAYER_INVALIDATE, LAYER_ADD, SCREEN_UPDATE,
              BITMAP_CLEAR, BITMAP_BLIT, BITMAP_BLIT_TRANSPARENT, SND_PLAY, SND_STOP,
              SND_RELEASE_ALL, SND_LOAD_TABLE, MUSIC_START, MUSIC_CLEAR,
              CURSOR_LAYER_SHOW, RESOURCE_BEGIN, RESOURCE_READ, RESOURCE_READ_HDR,
              RESOURCE_FREE_BODY, FLIC_CLOSE, UI_INPUT_INIT, UI_EVENT_PUMP, EVT_PUMP,
              PACKET_TICK, SCORE_TICK_INCOME, TEXT_COLOR_BASE, PALETTE_SET,
              PALETTE_FADE_IN, PALETTE_FADE_OUT, VICTORY_DIALOG, DEFEAT_DIALOG,
              GDS_FREE, MISSION_DEFEAT, NET_SEND_CONTROL):
        stub(emu, a, 0, log)
    stub(emu, TEXT_WIDTH, 10, log)
    stub(emu, SND_LOAD_TABLE, 0, log)
    stub(emu, STRLEN, 0, log)
    stub(emu, GDS_ALLOC, emu.alloc(0x20000), log)
    stub(emu, FLIC_OPEN, 1, log, pops=8)
    stub(emu, FLIC_REWIND, 1, log)
    stub(emu, FLIC_NEXT, 1, log)
    stub(emu, FLIC_RESTART, 1, log)
    stub(emu, RANK_NAME, 0x57000, log)
    stub(emu, SELECTION_FIRST, 0, log)
    stub(emu, SELECTION_NEXT, 0, log)


def sprintf_stub(emu, log=None):
    """Model `%ld` into the destination (the real clib sprintf is not needed
    for these tests and would run its full formatting path)."""
    def fn(e):
        sp = e.reg("esp")
        slots = [e.u32(sp + 4 + 4 * i) for i in range(3)]
        # the format is the slot that points at a small string like "%ld"
        fmt_at = None
        for i, v in enumerate(slots):
            try:
                raw = bytes(e.read(v, 4))
            except Exception:
                continue
            if raw[:3] == b"%ld":
                fmt_at = i
                break
        assert fmt_at is not None, [hex(v) for v in slots]
        rest = [v for i, v in enumerate(slots) if i != fmt_at]
        val = min(rest)
        buf = max(rest) if min(rest) == val and max(rest) != val else min(rest)
        buf = [v for v in rest if v != val][0]
        if val >= 0x80000000:
            val -= 1 << 32
        text = str(val).encode()
        e.write(buf, text + b"\0")
        if log is not None:
            log.append("sprintf")
        return len(text)
    emu.stubs[SPRINTF] = fn


def load(emu, name):
    return cemu.load(emu, os.path.join(AREA, name))


def unit_array(emu):
    """Allocate the 200-record unit array and publish its pointer at 0x59640."""
    base = emu.alloc(200 * UNIT_SIZE)
    u32(emu, UNIT_ARRAY, 0, base)
    return base


def unit(emu, slot, type=2, owner=0, px=0, py=0, flags=0, flags2=0, tx=0, ty=0):
    a = u32(emu, UNIT_ARRAY) + slot * UNIT_SIZE
    u16(emu, a, 0x00, px)
    u16(emu, a, 0x02, py)
    u16(emu, a, 0x0A, tx)
    u16(emu, a, 0x0C, ty)
    u16(emu, a, 0x0E, flags2)
    u16(emu, a, 0x10, flags)
    emu.write(a + 0x1B, bytes([type]))
    emu.write(a + 0x1E, bytes([owner]))
    return a


# ------------------------------------------------------------------- T3

def _matched_files():
    funcs, _, _ = symbols.load()
    return sorted({e["src"] for e in funcs.values()
                   if e.get("src", "").startswith("src/mod_2efd0/")})


@pytest.fixture(scope="module")
def prog():
    return analysis.run()


@pytest.mark.parametrize("src", _matched_files())
def test_matched_c(src, prog):
    """Every `src =` file of this area still matches the original (T3)."""
    out = path("build", "mod_2efd0", "t3_" + os.path.basename(src) + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, match.file_cflags(src), out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, (src, bad)


# ------------------------------------------------------------------- T4


def test_t4_issue_order_at():
    """0x2f0a8 IssueOrderAt: NetSendOrder(x, y, unit) and, on the local
    machine only, the cursor refresh for the new selection."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    cm = load(emu, "issue_order_at_reference.c")
    for slot, x, y, target in ((0, 3, 4, 0), (1, 0, 0xFFFF, 0x1234), (0, 0x7FFF, -3, 0x5678)):
        u32(emu, 0x5A11A, 0, slot)
        diffs = cemu.run_pair(emu, 0x2F0A8, cm, "IssueOrderAt_", x, y, target,
                              watch=[(0x5A11A, 2)], out_regs=())
        assert diffs == [], (slot, x, y, diffs)


def test_t4_selection_box_track():
    """0x2f0c8 SelectionBoxTrack: min/max of the press anchor and the current
    mouse position, the box size and the visible flag."""
    emu = Emu()
    cm = load(emu, "selection_box_track_reference.c")
    for ax, ay, mx, my in ((100, 50, 120, 80), (200, 90, 150, 40), (10, 10, 10, 10),
                           (-5, 7, 30, 0)):
        u16(emu, SELECTION_BOX, 0, ax & 0xFFFF)
        u16(emu, SELECTION_BOX, 2, ay & 0xFFFF)
        # the Event record is 12 bytes at a scratch address
        ev = emu.alloc(16)
        u16(emu, ev, 0, 1)
        u16(emu, ev, 4, mx & 0xFFFF)
        u16(emu, ev, 6, my & 0xFFFF)
        diffs = cemu.run_pair(emu, 0x2F0C8, cm, "SelectionBoxTrack_", ev,
                              watch=[(SELECTION_BOX, 18)], out_regs=())
        assert diffs == [], ((ax, ay, mx, my), diffs)


def test_t4_selection_box_begin():
    """0x2f350 SelectionBoxBegin: the guards (modal input, placement box), the
    callback installation and the anchor = press position."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    cm = load(emu, "selection_box_begin_reference.c")
    ev = emu.alloc(16)
    u16(emu, ev, 4, 77)
    u16(emu, ev, 6, 88)
    for blocked, placing in ((0, 0), (1, 0), (0, 1)):
        emu.stubs[INPUT_BLOCKED] = lambda e, b=blocked: b
        emu.stubs[PLACE_BOX_ACTIVE] = lambda e, p=placing: p
        diffs = cemu.run_pair(emu, 0x2F350, cm, "SelectionBoxBegin_", ev,
                              watch=[(SELECTION_BOX, 6), (0x5940C, 4), (0x59414, 4),
                                     (0x5941C, 4), (0x59424, 4)],
                              out_regs=())
        assert diffs == [], ((blocked, placing), diffs)


def test_t4_selection_box_frame():
    """0x2f15c SelectionBoxFrame: the box is converted to map pixels and the
    units inside it are collected; SelectionSet receives the list."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    cm = load(emu, "selection_box_frame_reference.c")
    unit_array(emu)
    # three own creatures and one enemy building inside the viewport
    unit(emu, 0, type=3, owner=0, px=0x60, py=0x30)
    unit(emu, 1, type=4, owner=0, px=0x70, py=0x40)
    unit(emu, 2, type=0x20, owner=0, px=0x68, py=0x38)
    unit(emu, 3, type=3, owner=1, px=0x6C, py=0x3C)
    u16(emu, SELECTION_BOX, 0, 0x50)      # anchor
    u16(emu, SELECTION_BOX, 2, 0x20)
    u16(emu, SELECTION_BOX, 14, 1)
    u16(emu, 0x500D0, 0, 0)               # map_scroll_x
    u16(emu, 0x500D2, 0, 0)               # map_scroll_y
    u16(emu, SELECTION_LOCAL, 0, 1)
    u16(emu, MOD_ALL, 0, 0)
    u16(emu, MOD_ADD, 0, 0)
    u32(emu, 0x5A11A, 0, 0)
    base = u32(emu, UNIT_ARRAY)
    emu.stubs[SELECTION_FIRST] = lambda e: base
    emu.stubs[SELECTION_NEXT] = lambda e: 0
    ev = emu.alloc(16)
    u16(emu, ev, 0, 1)
    u16(emu, ev, 4, 0xC0)
    u16(emu, ev, 6, 0x90)
    diffs = cemu.run_pair(emu, 0x2F15C, cm, "SelectionBoxFrame_", ev,
                          watch=[(SELECTION_BOX, 18)], out_regs=())
    assert diffs == [], diffs



def test_t4_end_check_elimination():
    """0x2f4c0 EndCheckElimination: the cheat bits, the "enemy gone" victory
    and the "own side gone" defeat, in both the link and the screen mode."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    cm = load(emu, "end_check_elimination_reference.c")
    cases = [
        (0, 0, 1, 1, 0, 0, 3),        # nothing happens
        (0, 0, 1, 1, 0, 1, 3),        # own buildings gone -> defeat screen
        (0, 0, 0, 0, 1, 1, 3),        # enemy gone -> victory screen
        (0, 0, 0, 0, 1, 1, 3),
        (0x100, 0, 1, 1, 1, 1, 7),    # "yours truly" -> victory
        (0, 0x80, 1, 1, 1, 1, 6),     # "crushing defeat"
    ]
    for cheat, mode, men0, bld0, men1, bld1, gm in cases:
        u32(emu, CHEAT_FLAGS, 0, cheat)
        u16(emu, GAME_MODE, 0, gm)
        u16(emu, PLAYER_MEN, 0, men0)
        u16(emu, PLAYER_MEN, 2, men1)
        u16(emu, PLAYER_BUILDINGS, 0, bld0)
        u16(emu, PLAYER_BUILDINGS, 2, bld1)
        diffs = cemu.run_pair(emu, 0x2F4C0, cm, "EndCheckElimination_",
                              watch=[(GAME_MODE, 2), (END_ACTION, 4)],
                              out_regs=())
        assert diffs == [], (cheat, mode, men0, bld0, men1, bld1, diffs)


def test_t4_end_check_survive():
    """0x2f694 EndCheckSurvive: the unit-cap victory, the town-hall/worker
    defeat paths and the gold/lumber recovery gate."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    cm = load(emu, "end_check_survive_reference.c")
    cases = [
        # cap, halls, hallptr, workers, men, gold, lumber, train, count
        (0, 0, 0, 0, 0, 0, 0, 0, 0),
        (6, 2, 1, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0x190, 0, 0, 0),
        (0, 0, 1, 0, 0, 0x190, 0, 0, 0),
        (0, 0, 1, 1, 0, 0, 0, 0, 0),
        (0, 0, 0, 1, 0, 0x190, 0, 0, 0),
        (0, 0, 0, 1, 0, 0x190, 0x190, 0, 0),
        (0, 0, 0, 0, 1, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 1, 0),
        (0, 0, 0, 0, 0, 0, 0, 0, 1),
    ]
    for cap, halls, hall, workers, men, gold, lumber, train, count in cases:
        u16(emu, PLAYER_CAP, 0, cap)
        u16(emu, PLAYER_HALLS, 0, halls)
        u32(emu, PLAYER_TOWN_HALL, 0, hall)
        u16(emu, PLAYER_WORKERS, 0, workers)
        u16(emu, PLAYER_MEN, 0, men)
        u32(emu, GOLD, 0, gold)
        u32(emu, LUMBER, 0, lumber)
        u16(emu, TRAINING, 0, train)
        u16(emu, UNIT_COUNT, 0, count)
        u32(emu, CHEAT_FLAGS, 0, 0)
        diffs = cemu.run_pair(emu, 0x2F694, cm, "EndCheckSurvive_",
                              watch=[(END_ACTION, 4), (GAME_MODE, 2)],
                              out_regs=())
        assert diffs == [], (cap, halls, hall, workers, men, gold, lumber, diffs)



def test_t4_mission_start_check():
    """0x2f788 MissionStartCheck: the objective word selects the end check and
    the palette-cycle bit."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    cm = load(emu, "mission_start_check_reference.c")
    for objectives, demo in ((0, 0), (1, 0), (0x20, 0), (0x80, 0), (0xFF, 0),
                             (0, 1), (0x21, 1)):
        u16(emu, SCENARIO_OBJECTIVES, 0, objectives)
        u16(emu, 0x5152C, 0, demo)
        diffs = cemu.run_pair(emu, 0x2F788, cm, "MissionStartCheck_",
                              watch=[(END_ACTION, 4), (END_TIMER, 2),
                                     (0x628A0, 2), (0x5A868, 2)],
                              out_regs=())
        assert diffs == [], (objectives, demo, diffs)


def test_t4_format_number():
    """0x2f830 FormatNumber: thousands separators for 0..millions."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    sprintf_stub(emu, log)
    cm = load(emu, "format_number_reference.c")
    buf = emu.alloc(0x80)
    for value, expect in ((0, " 0"), (5, " 5"), (999, " 999"),
                          (1000, " 1,000"), (12345, " 12,345"),
                          (123456, " 123,456"), (1234567, " 1,234,567")):
        emu.write(buf, b"\0" * 0x40)
        emu.write(buf + 0x20, b"\0" * 0x40)
        u32(emu, buf, 0) or emu.write(buf, b"1234567\0" + b"\0" * 0x39)
        diffs = cemu.run_pair(emu, 0x2F830, cm, "FormatNumber_", buf, value,
                              buf + 0x20, watch=[(buf, 0x40), (buf + 0x20, 0x40)],
                              out_regs=())
        assert diffs == [], (value, diffs)


def test_t4_draw_number():
    """0x2f878/0x2f8bc DrawNumberRight/DrawNumberCentre: the x adjustment
    from the measured width (stubbed TextWidth) reaches DrawText."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    sprintf_stub(emu, log)
    right = load(emu, "draw_number_right_reference.c")
    centre = load(emu, "draw_number_centre_reference.c")
    for fn, cm in (("DrawNumberRight_", right), ("DrawNumberCentre_", centre)):
        for x, y, value in ((100, 20, 1234), (0, 0, 0), (300, 190, 999999)):
            diffs = cemu.run_pair(emu, 0x2F878 if fn.startswith("DrawNumberRight")
                                  else 0x2F8BC, cm, fn, x, y, value,
                                  out_regs=())
            assert diffs == [], (fn, x, y, value, diffs)


def test_t4_end_screen_sound_id():
    """0x2fa30 EndScreenSoundId: the defeat id and the four race tables."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    cm = load(emu, "end_screen_sound_id_reference.c")
    for gm, race, enemy in ((7, 0, 0), (7, 1, 0), (6, 0, 0), (6, 0, 1),
                            (6, 1, 0), (6, 1, 1)):
        u16(emu, GAME_MODE, 0, gm)
        u16(emu, 0x50088, 0, race)
        u16(emu, 0x5008A, 0, enemy)
        u32(emu, 0x50D7C, 0, 12345)
        diffs = cemu.run_pair(emu, 0x2FA30, cm, "EndScreenSoundId_",
                              watch=[(0x50D7C, 4)], out_regs=("eax",))
        assert diffs == [], (gm, race, enemy, diffs)


def test_t4_end_screen_animate():
    """0x2f9b4 EndScreenAnimate: the count-up towards the target, the clamp
    and the return value."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    stub(emu, 0x2F938, 0, log)
    cm = load(emu, "end_screen_animate_reference.c")
    for value, target, step in ((0, 100, 1), (100, 100, 1), (0, 1000, 500),
                                (999, 1000, 500), (5, 0, 1)):
        u32(emu, END_VALUES, 0, value)
        u32(emu, END_TARGETS, 0, target)
        u16(emu, VALUE_STEP, 0, step)
        diffs = cemu.run_pair(emu, 0x2F9B4, cm, "EndScreenAnimate_",
                              watch=[(END_VALUES, 4)], out_regs=("eax",))
        assert diffs == [], (value, target, step, diffs)




def test_t4_end_screen_movie():
    """0x2fac4 EndScreenMovie: the callback installation, the first sound and
    the immediate exit when EndScreenStop already set the done flag."""
    emu = Emu()
    log = []
    stub_all(emu, log)
    cm = load(emu, "end_screen_movie_reference.c")

    def pump(e):
        u16(e, END_DONE, 0, 1)
        return 0
    emu.stubs[UI_EVENT_PUMP] = pump
    u16(emu, GAME_MODE, 0, 6)
    screen = emu.alloc(16)
    u16(emu, screen, 0, 320)
    u16(emu, screen, 2, 200)
    u32(emu, screen, 4, 0x600000)
    diffs = cemu.run_pair(emu, 0x2FAC4, cm, "EndScreenMovie_", 0x600000, screen,
                          watch=[(END_DONE, 2), (END_TICKS, 2), (MOVIE_STATE, 2),
                                 (0x59414, 4), (0x5941C, 4), (0x59400, 40),
                                 (0x59420, 4), (0x5AB8C, 2)],
                          out_regs=())
    assert diffs == [], diffs


# ----------------------------------------------------------- structural


def test_module_bounds_and_tables():
    """The module data documented in the docs page: the box field order, the
    end-screen tables and the sizes the code indexes."""
    p = analysis.run()
    starts = sorted(f["start"] for f in p.functions)
    assert 0x2EFD0 in starts and 0x3024C not in [s for s in starts if s < 0x30300]

    img = le.load().loaded_image()
    l = le.load()

    def w(a):
        return int.from_bytes(l.read(a, 2, img), "little")

    # the 13 score rows: three columns of four plus the centred score line
    assert [w(VALUE_X + 2 * i) for i in range(13)] == \
        [87, 87, 87, 87, 187, 187, 187, 187, 285, 285, 285, 285, 48]
    assert [w(VALUE_Y + 2 * i) for i in range(13)] == \
        [75, 85, 107, 117, 75, 85, 107, 117, 75, 85, 107, 117, 25]
    # the count-up steps
    assert [w(VALUE_STEP + 2 * i) for i in range(13)] == \
        [1, 1, 1, 1, 1, 1, 1, 1, 500, 500, 200, 200, 100]
    # the panel rectangle and the full-screen layer rectangle
    assert [w(END_PANEL_RECT + 2 * i) for i in range(6)] == [0, 0, 0xB7, 0x6F, 0xB8, 0x70]
    assert [w(FULL_SCREEN_RECT + 2 * i) for i in range(6)] == [0, 0, 319, 199, 320, 200]
    # the sound table is 0-terminated
    assert w(END_SOUND_IDS) == 487 and w(END_SOUND_IDS + 20) == 0
    # is_unit mask: creatures 0..0x1f, buildings 0x20..0x33
    assert all(w(TYPE_IS_CREATURE + 2 * i) == 1 for i in range(0x20))
    assert all(w(TYPE_IS_CREATURE + 2 * i) == 0 for i in range(0x20, 0x34))
    # the map view rectangle used by MouseSetRange
    assert [w(MAP_VIEW_RECT + 2 * i) for i in range(4)] == [0x48, 0xC, 0x137, 0xBB]


def test_selection_box_layout():
    """The selection box is a 9-word struct (anchor, min, max, w, h, visible)
    at 0x5a7d0; SelectionBoxDraw reads min_x/min_y, min_y is the high half of
    the dword at 0x5a7d4 and min_x the high half of the dword at 0x5a7d2."""
    p = analysis.run()
    insns = {a: f"{i.mnemonic} {i.op_str}" for a, i in p.insns.items()}
    assert "mov edx, dword ptr [0x5a7d4]" in insns[0x2F402]
    assert "mov eax, dword ptr [0x5a7d2]" in insns[0x2F40B]
    assert "mov word ptr [0x5a7e0], 1" in insns[0x2F14F]
