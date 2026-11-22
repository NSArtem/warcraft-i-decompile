"""Game logic: STATUS.C (0x27b20..0x295d0), the unit status / command panel.

1. Every C file the symbol database builds (`src =` in
   analysis/symbols/status.toml) still reproduces the original bytes,
   relocation targets and module-local data (T3, `wc1.match`).
2. T4: the reference C of the panel functions runs against the original under
   `wc1.cemu` on identical inputs - `cemu.load` compiles the file with its
   codegen-flags and relocates it against the symbol database, `run_pair` runs
   both sides and compares the return register and watched memory (the callees
   with side effects are stubbed and their arguments recorded, as in
   tests/test_cmd_123f0.py).
3. Structural checks of the panel data: the string pool, the command card of
   the footman, the button geometry and the module boundary.
"""
import os
import struct

import pytest

from wc1 import cemu, codegen_sweep, match, path, symbols
from wc1.emu import Emu

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "status")

# --------------------------------------------------------------- addresses
UNIT_SIZE = 0x5C
SELECTED_UNITS = 0x5A0F0
SELECTION_INDEX = 0x5A114
PLAYER_SLOT = 0x5A11A
STATUS_BUTTON = 0x5A2C0
STATUS_UNIT = 0x5A2C4
STATUS_UNIT_REQ = 0x5A2C8
STATUS_BUTTON_RECT = 0x5A2CC
STATUS_DIRTY = 0x5A2D0
STATUS_MEN_USED = 0x5A2D4
STATUS_LOCK = 0x5A2D6
STATUS_MEN_GROWN = 0x5A2D8
STATUS_VISIBLE = 0x5A2DA
STATUS_UNIT_TYPE = 0x5A2DC
STATUS_SEL_COUNT = 0x5A2DE
STATUS_PRESSED = 0x5A2E0
STATUS_FLAGS_CACHE = 0x5A2E3
STATUS_PROGRESS_CACHE = 0x5A2E4
STATUS_TEXT_PROD = 0x5A2E8
STATUS_TEXT_REPAIR = 0x5A268
STATUS_HP_CACHE = 0x5A2B8
STATUS_DAMAGE_CACHE = 0x5A260
STATUS_HELP_TEXT = 0x59500
STATUS_TEXT = 0x55148
SELECTION_COUNT = 0x5A110
PLAYER_MEN = 0x58E28
PLAYER_SUMMONED = 0x58DCE
PLAYER_FOOD = 0x58DE2
CUR_BITMAP = 0x55438
DIRTY_X1 = 0x5ACD0
UNIT_PANEL_TABLE = 0x549C4
COMMAND_BUTTON_RECT = 0x514E4
UNIT_NAMES = 0x54E54
STATUS_INFO_RECT = 0x53590
STATUS_INFO_BUTTON = 0x53AEC
SCENARIO_UNIT_MASK = 0x50004
PLAYER_UPGRADE = 0x50008
UPGRADE_LEVEL_COST = 0x51880
UNIT_MAX_HP = 0x51978
UNIT_LUMBER_COST = 0x51A84
UNIT_SUFFIX_TRAIN = 0x5506C
RESEARCH_TEXT = 0x550F8
SCORE_VALUE = 0x51A4C
FILL_RECT = 0x326A0
BITMAP_BLIT = 0x32410
BITMAP_BLIT_ALL = 0x33B00
BITMAP_BLIT_TRANS = 0x326F0
GRP_FRAME_BITMAP = 0x33110
DRAW_TEXT = 0x31DCC
TEXT_SET_COLOR_BASE = 0x32030
SCREEN_UPDATE = 0x321E8
DIRTY_RECT_UNION = 0x328C0
DIRTY_RECT_ADD_BOX = 0x33A30
SPRINTF = 0x31BE2
SET_HELP_TEXT = 0x19F80
MAP_INPUT_RESTORE = 0x1A328
SELECTION_FIRST = 0x25CC4
SELECTION_NEXT = 0x25C50
BUTTON_DRAW = 0x284A8
BUTTON_ALWAYS = 0x27B20
SELECTION_WORKERS_FALSE = 0x28090
CANCEL_UPGRADE = 0x28140
CANCEL_TRAINING = 0x28170
CANCEL_CONSTRUCTION = 0x281AC
CAN_BUILD_FARM = 0x27CC8
ACTION_MOVE = 0x20EC4
ACTION_STOP = 0x20E98
ACTION_ATTACK = 0x21030
OPEN_GAME_MENU = 0x281E8
NET_SEND_CONTROL = 0x21C20


# callees the symbol database does not name yet (their own areas own them):
# the reference C needs them to load, and the tests stub them.
EXTRA = {"MapInputRestore_": MAP_INPUT_RESTORE,
         "LayerFree_": 0x21CF0,
         "LayerAdd_": 0x21D0C,
         "SetCursor_": 0x13DD0,
         # 0x59424: the map view's fourth callback slot, cleared by
         # StatusPanelShow (published by the UI event layer, mod_16390)
         "_status_event_callback": 0x59424,
         # 0x19f80: the status chart's help-text setter (mod_19b80)
         "SetHelpText_": 0x19F80}


# ------------------------------------------------------------------ helpers
def load(emu, name):
    return cemu.load(emu, os.path.join(AREA, name), extra=EXTRA)

def _u8(emu, base, off, v):
    emu.write(base + off, bytes([v & 0xFF]))


def _u16(emu, base, off, v):
    emu.write(base + off, struct.pack("<H", v & 0xFFFF))


def _u32(emu, base, off, v):
    emu.write(base + off, struct.pack("<I", v & 0xFFFFFFFF))


def unit(emu, **kw):
    """A zeroed unit record in the emulator heap with the named fields set."""
    u = emu.alloc(UNIT_SIZE)
    emu.write(u, b"\x00" * UNIT_SIZE)
    for name, (off, size) in {"hp": (0x16, 2), "damage": (0x1A, 1), "type": (0x1B, 1),
                              "type_copy": (0x1C, 1), "owner": (0x1E, 1),
                              "order": (0x1F, 1), "sflags": (0x0E, 2), "flags": (0x10, 2),
                              "prod_type": (0x3E, 1), "progress": (0x46, 4),
                              "state": (0x49, 1), "dest": (0x4E, 1),
                              "target": (0x54, 4)}.items():
        if name in kw:
            v = kw[name]
            if size == 1:
                _u8(emu, u, off, v)
            elif size == 2:
                _u16(emu, u, off, v)
            else:
                _u32(emu, u, off, v)
    return u


def set_selection(emu, units, player=0):
    """Publish a selection: the iterator reads selected_units[player*16 + i]."""
    emu.write(SELECTED_UNITS, b"\x00" * 0x80)
    for i, u in enumerate(units):
        _u32(emu, SELECTED_UNITS + (player * 16 + i) * 4, 0, u)
    _u16(emu, SELECTION_INDEX, 0, 0)
    _u16(emu, PLAYER_SLOT, 0, player)
    _u16(emu, SELECTION_COUNT, 0, len(units))


def stub_call(emu, addr, nargs=4, size=0x20):
    """Replace a callee with a recorder: its register arguments land in a
    scratch block that the difftest watches."""
    rec = emu.alloc(size)
    emu.write(rec, b"\x00" * size)

    def fn(e):
        for k in range(nargs):
            e.put_u32(rec + 4 * k, e.reg(("eax", "edx", "ebx", "ecx")[k]))
        return 0

    emu.stubs[addr] = fn
    return rec


def stub_text(emu):
    """Record DrawText's (x, y) and the *text* of its string: the string lives
    in a stack buffer whose address legitimately differs between the two runs."""
    rec = emu.alloc(0x30)
    emu.write(rec, b"\x00" * 0x30)

    def fn(e):
        e.put_u32(rec + 0, e.reg("eax"))
        e.put_u32(rec + 4, e.reg("edx"))
        src = e.reg("ebx")
        text = b""
        for k in range(0x20):
            ch = e.read(src + k, 1)
            if ch == b"\x00":
                break
            text += ch
        e.write(rec + 8, text)
        return 0

    emu.stubs[DRAW_TEXT] = fn
    return rec


def stub_sprintf(emu):
    """A tiny sprintf model for the formats STATUS.C uses (%d, %ld, %s)."""
    fmt = emu.alloc(8)
    out = emu.alloc(0x80)
    emu.write(fmt, b"%s\0")

    def fn(e):
        sp = e.reg("esp")
        dst = e.u32(sp + 4)
        f = e.cstr(e.u32(sp + 8))
        args = [e.u32(sp + 12), e.u32(sp + 16), e.u32(sp + 20)]
        ai = 0
        res = b""
        i = 0
        while i < len(f):
            if f[i:i + 1] == b"%":
                spec = f[i + 1:i + 2]
                if spec == b"d":
                    res += str(args[ai] & 0xFFFF).encode()
                    ai += 1
                    i += 2
                    continue
                if spec == b"l" and f[i + 2:i + 3] == b"d":
                    res += str(args[ai]).encode()
                    ai += 1
                    i += 3
                    continue
                if spec == b"s":
                    res += e.cstr(args[ai])
                    ai += 1
                    i += 2
                    continue
            res += f[i:i + 1]
            i += 1
        e.write(dst, res + b"\0")
        return len(res)

    emu.stubs[SPRINTF] = fn
    return out


def button(emu, icon=0, face=0x21, available=BUTTON_ALWAYS, key=0x32, kind=0, arg=0,
           action=ACTION_MOVE, label=0):
    """A command-button record in the emulator heap (0x14 bytes, packed)."""
    b = emu.alloc(0x14)
    emu.write(b, b"\x00" * 0x14)
    _u16(emu, b, 0x00, icon)
    _u16(emu, b, 0x02, face)
    _u32(emu, b, 0x04, available)
    _u32(emu, b, 0x08, label)
    _u8(emu, b, 0x0C, key)
    _u8(emu, b, 0x0D, kind)
    _u8(emu, b, 0x0E, arg)
    _u32(emu, b, 0x0F, action)
    return b


def rect(emu, x1, y1, x2, y2, w=None, h=None):
    r = emu.alloc(12)
    emu.write(r, struct.pack("<6h", x1, y1, x2, y2, x2 - x1 + 1 if w is None else w,
                             y2 - y1 + 1 if h is None else h))
    return r


# ------------------------------------------------------- T3: matched files
def _matched_files():
    funcs, _, _ = symbols.load()
    return sorted({e["src"] for e in funcs.values() if e.get("src", "").startswith("src/status/")})


@pytest.fixture(scope="module")
def prog():
    return codegen_sweep.program()


@pytest.mark.parametrize("src", _matched_files())
def test_matched_c(src, prog):
    """Every `src =` file of this area still matches the original (T3)."""
    out = path("build", "status", "t3_" + os.path.basename(src) + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, match.file_cflags(src), out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, (src, bad)


def test_every_area_function_has_an_entry():
    """All 81 discovered starts of the range are in the database and named."""
    from wc1 import analysis
    p = analysis.run()
    starts = {f["start"] for f in p.functions if 0x27B20 <= f["start"] < 0x295D0}
    funcs, _, _ = symbols.load()
    assert len(starts) == 81
    for a in starts:
        assert a in funcs, hex(a)
        assert not funcs[a]["name"].startswith("fn_"), hex(a)


# ---------------------------------------------------- structural (no emu)
def test_status_string_pool():
    """The STATUS.C string pool 0x57d50..0x57dd9 names itself; the module list
    (analysis/modules.toml) records the same slice as referenced only here."""
    from wc1 import analysis
    p = analysis.run()
    d = p.data.data
    base = p.data.base

    def cstr(a):
        s = b""
        while d[a - base] != 0:
            s += bytes([d[a - base]])
            a += 1
        return s

    for addr, text in [(0x57D50, b"food usage:"), (0x57D5C, b"used %d"),
                       (0x57D64, b"grown %d"), (0x57D70, b"gold left"),
                       (0x57D7C, b"%ld"), (0x57D80, b"training a%s"),
                       (0x57D90, b"building a wall"),
                       (0x57DA0, b"full repairs will cost %d gold & lumber"),
                       (0x57DC8, b"carrying gold"), (0x57DD8, b"carrying lumber"),
                       (0x57DE8, b"Select target")]:
        assert cstr(addr) == text, hex(addr)


def test_footman_command_card():
    """unit_panel_table[0] is the footman/grunt card: 7 buttons, the record at
    0x53b00 = icon 0/face 0x21/'move'/key 0x32/action 0x20ec4."""
    from wc1 import analysis
    p = analysis.run()
    img = p.image[p.data.index]
    base = p.data.base

    def w(a):
        return struct.unpack_from("<H", img, a - base)[0]

    def dw(a):
        return struct.unpack_from("<I", img, a - base)[0]

    def cstr(a):
        i = a
        s = b""
        while img[i - base] != 0:
            s += bytes([img[i - base]])
            i += 1
        return s

    assert w(UNIT_PANEL_TABLE) == 7                     # footman
    assert dw(UNIT_PANEL_TABLE + 2) == 0x53B00
    assert dw(UNIT_PANEL_TABLE + 6) == 0x281F4          # UnitPanelStateChanged
    assert dw(0x53B00) == 0x0021_0000                   # icon 0, face 0x21
    assert dw(0x53B04) == 0x27B20                       # ButtonAlwaysAvailable
    assert cstr(dw(0x53B08)) == b"@1m@2ove"
    assert img[0x53B0C - base] == 0x32                  # 'M' scan code
    assert dw(0x53B0F) == 0x20EC4                       # the order-layer action
    # the farm and the gold mine carry the extra-line painters
    assert dw(UNIT_PANEL_TABLE + 14 * 0x20 + 10) == 0x28298
    assert dw(UNIT_PANEL_TABLE + 14 * 0x32 + 10) == 0x2839C
    # the panel geometry: six buttons, two columns at x 2/0x24, rows 0x74..0xa2
    assert [struct.unpack_from("<6h", img, COMMAND_BUTTON_RECT - base + 12 * i)
            for i in range(2)] == [(2, 0x74, 0x21, 0x8A, 0x20, 0x17),
                                   (0x24, 0x74, 0x43, 0x8A, 0x20, 0x17)]


def test_panel_rect_and_module_boundary():
    """The panel is the 72x128 rect at (0,72) and STATUS.C ends at 0x295d0."""
    from wc1 import analysis
    import tomllib
    p = analysis.run()
    img = p.image[p.data.index]
    base = p.data.base
    assert struct.unpack_from("<6h", img, 0x53570 - base) == (0, 0x48, 0x47, 0xC7, 0x48, 0x80)
    mods = tomllib.load(open(path("analysis", "modules.toml"), "rb"))["module"]
    m = next(m for m in mods if m["name"] == "STATUS.C")
    assert (m["start"], m["end"]) == (0x27B20, 0x295D0)
    starts = {f["start"] for f in p.functions if m["start"] <= f["start"] < m["end"]}
    assert max(starts) == 0x29450


# ------------------------------------------------------- T4: difftests
def test_t4_can_harvest():
    """0x27b28 CanHarvest: empty selection, all workers, a carrying worker, a
    non-worker and mixed selections; the selection iterator's state and the
    return value are compared."""
    emu = Emu()
    cm = load(emu, "selection_reference.c")
    workers = [unit(emu, type=2), unit(emu, type=3)]
    for units in ([], [workers[0]], workers, [unit(emu, type=2, state=0x20)],
                  [unit(emu, type=0)], [unit(emu, type=2), unit(emu, type=6)]):
        set_selection(emu, units)
        diffs = cemu.run_pair(emu, 0x27B28, cm, "CanHarvest_",
                              watch=[(SELECTION_INDEX, 2)], out_regs=("eax",))
        assert diffs == [], (len(units), diffs)


def test_t4_can_return_goods():
    """0x27b68 CanReturnGoods: the selection count gate, the carrying byte and
    the town hall pointer."""
    emu = Emu()
    cm = load(emu, "selection_reference.c")
    for count, state, hall in [(0, 0x20, 0), (1, 0x20, 0), (1, 0x00, 0x12345678),
                               (1, 0x20, 0x12345678), (1, 0x80, 0x12345678),
                               (2, 0x20, 0x12345678)]:
        u = unit(emu, type=2, state=state)
        _u32(emu, STATUS_UNIT, 0, u)
        _u16(emu, SELECTION_COUNT, 0, count)
        _u32(emu, 0x58DB0, 0, hall)
        diffs = cemu.run_pair(emu, 0x27B68, cm, "CanReturnGoods_",
                              watch=[(SELECTION_COUNT, 2)], out_regs=("eax",))
        assert diffs == [], (count, state, hall, diffs)


def test_t4_selection_is_workers():
    """0x28074 SelectionHasNoWorkers (the whole function, discovery splits it at
    0x28090/0x28093): available while no selected unit is a peasant/peon."""
    emu = Emu()
    cm = load(emu, "selection_reference.c")
    cases = [[], [2], [3], [0], [2, 2], [2, 3], [2, 0], [0x20], [2, 3, 3, 3], [0, 1]]
    for types in cases:
        set_selection(emu, [unit(emu, type=t) for t in types])
        diffs = cemu.run_pair(emu, 0x28074, cm, "SelectionHasNoWorkers_",
                              watch=[(SELECTION_INDEX, 2)], out_regs=("eax",))
        assert diffs == [], (types, diffs)


def test_t4_unit_panel_state_changed():
    """0x281f4 UnitPanelStateChanged: cached hp/damage per slot and the shown
    unit type; the caches are watched so both sides see the same input."""
    emu = Emu()
    cm = load(emu, "panel_state_reference.c")
    u = unit(emu, type=0, hp=60, damage=0xFF, type_copy=0)
    _u32(emu, STATUS_UNIT, 0, u)
    watch = [(STATUS_HP_CACHE, 8), (STATUS_DAMAGE_CACHE, 8), (STATUS_UNIT_TYPE, 2),
             (SELECTION_INDEX, 2)]
    for n, hp, dmg, shown, typ in [(0, 60, 0xFF, 0, 0), (1, 60, 0xFF, 0, 0),
                                   (1, 59, 0xFF, 0, 0), (1, 60, 0xAA, 0, 0),
                                   (1, 60, 0xFF, 3, 0), (2, 60, 0xFF, 0, 0)]:
        set_selection(emu, [u] * n)
        _u16(emu, STATUS_HP_CACHE, 0, hp)
        _u16(emu, STATUS_DAMAGE_CACHE, 0, dmg)
        _u16(emu, STATUS_UNIT_TYPE, 0, shown)
        u2 = unit(emu, type=0, hp=hp, damage=dmg, type_copy=typ)
        set_selection(emu, [u2] * n)
        _u16(emu, STATUS_HP_CACHE, 0, hp)
        _u16(emu, STATUS_DAMAGE_CACHE, 0, dmg)
        _u16(emu, STATUS_UNIT_TYPE, 0, shown)
        diffs = cemu.run_pair(emu, 0x281F4, cm, "UnitPanelStateChanged_",
                              watch=watch, out_regs=("eax",))
        assert diffs == [], (n, hp, dmg, shown, diffs)


def test_t4_farm_panel_changed():
    """0x28254 FarmPanelChanged: the used/grown caches, then the standard
    callback (which reads the selection and the shown type)."""
    emu = Emu()
    cm = load(emu, "panel_state_reference.c")
    u = unit(emu, type=0x20, hp=60, damage=0xFF, type_copy=0x20)
    _u32(emu, STATUS_UNIT, 0, u)
    watch = [(STATUS_MEN_USED, 2), (STATUS_MEN_GROWN, 2), (STATUS_HP_CACHE, 8),
             (STATUS_DAMAGE_CACHE, 8), (STATUS_UNIT_TYPE, 2), (SELECTION_INDEX, 2)]
    for men, summ, food, cached_used, cached_grown in [
            (4, 0, 16, 4, 16), (4, 0, 16, 3, 16), (4, 1, 16, 3, 16),
            (0, 0, 0, 0, 0), (0xFFFF, 0, 0xFFFF, 0xFFFF, 0xFFFF),
            (5, 2, 8, 5, 8)]:
        _u16(emu, PLAYER_MEN, 0, men)
        _u16(emu, PLAYER_SUMMONED, 0, summ)
        _u16(emu, PLAYER_FOOD, 0, food)
        _u16(emu, STATUS_MEN_USED, 0, cached_used)
        _u16(emu, STATUS_MEN_GROWN, 0, cached_grown)
        set_selection(emu, [u])
        _u16(emu, PLAYER_MEN, 0, men)
        _u16(emu, PLAYER_SUMMONED, 0, summ)
        _u16(emu, PLAYER_FOOD, 0, food)
        _u16(emu, STATUS_MEN_USED, 0, cached_used)
        _u16(emu, STATUS_MEN_GROWN, 0, cached_grown)
        diffs = cemu.run_pair(emu, 0x28254, cm, "FarmPanelChanged_",
                              watch=watch, out_regs=("eax",))
        assert diffs == [], (men, summ, food, cached_used, diffs)


def test_t4_research_cost():
    """0x28c60 ResearchCost: every row 0..9 for both players, each upgrade level
    0..2 and the spell rows; the *level pointer target is watched."""
    emu = Emu()
    cm = load(emu, "panel_text_reference.c")
    out = emu.alloc(4)
    watch = [(PLAYER_UPGRADE, 50), (out, 4)]
    for player in (0, 1):
        for row in range(10):
            for level in (0, 1, 2):
                emu.write(PLAYER_UPGRADE, bytes([level]) * 10 + b"\x00" * 40)
                _u32(emu, out, 0, 0)
                diffs = cemu.run_pair(emu, 0x28C60, cm, "ResearchCost_", player, row, out,
                                      watch=watch, out_regs=("eax",))
                assert diffs == [], (player, row, level, diffs)


def test_t4_health_bar_draw():
    """0x2864c HealthBarDraw: the 27-pixel bar over the hp range of several unit
    types, with the FillRect arguments and draw_color compared."""
    emu = Emu()
    cm = load(emu, "draw_reference.c")
    rec = stub_call(emu, FILL_RECT, 4)
    emu.stubs[FILL_RECT].__doc__ = "FillRect recorder"
    for type_ in (0, 2, 4, 6, 0x20):
        maxhp = struct.unpack("<H", emu.read(UNIT_MAX_HP + 2 * type_, 2))[0]
        for hp in (0, 1, maxhp // 4, maxhp // 2, 3 * maxhp // 4, maxhp - 1, maxhp):
            u = unit(emu, type=type_, hp=hp)
            diffs = cemu.run_pair(emu, 0x2864C, cm, "HealthBarDraw_", 0x25, 0x14, u,
                                  watch=[(rec, 16), (0x5AD30, 1)], out_regs=())
            assert diffs == [], (hex(type_), hp, diffs)


def test_t4_health_bar_draw_single():
    """0x28700 HealthBarDrawSingle: the state-1 bar length for every damage byte
    value around the 255 scale."""
    emu = Emu()
    cm = load(emu, "draw_reference.c")
    rec = stub_call(emu, FILL_RECT, 4)
    for damage in (0, 1, 2, 10, 100, 127, 200, 254, 255):
        u = unit(emu, damage=damage)
        _u32(emu, STATUS_UNIT, 0, u)
        diffs = cemu.run_pair(emu, 0x28700, cm, "HealthBarDrawSingle_",
                              watch=[(rec, 16), (0x5AD30, 1)], out_regs=())
        assert diffs == [], (damage, diffs)


def test_t4_progress_bar_draw():
    """0x28770 ProgressBarDraw: the construction bar and its icon blit."""
    emu = Emu()
    cm = load(emu, "draw_reference.c")
    rec = stub_call(emu, FILL_RECT, 4)
    icon = stub_call(emu, BITMAP_BLIT_TRANS, 3)
    for damage in (0, 1, 5, 60, 128, 254, 255):
        u = unit(emu, damage=damage)
        _u32(emu, STATUS_UNIT, 0, u)
        diffs = cemu.run_pair(emu, 0x28770, cm, "ProgressBarDraw_",
                              watch=[(rec, 16), (icon, 12), (0x5AD30, 1)], out_regs=())
        assert diffs == [], (damage, diffs)


def test_t4_button_available():
    """0x28434 ButtonAvailable: the alive/dead/busy gates and the predicate
    call with the "not a building" argument."""
    emu = Emu()
    cm = load(emu, "button_available.c")
    explicit = stub_call(emu, CAN_BUILD_FARM, 1)
    for flags, sflags, type_, avail in [
            (0, 0, 0, SELECTION_WORKERS_FALSE), (0, 0, 0, BUTTON_ALWAYS),
            (0, 0, 0x20, CAN_BUILD_FARM), (0, 0, 5, CAN_BUILD_FARM),
            (0x80, 0x10, 0, CANCEL_TRAINING), (0x80, 0x10, 0, CANCEL_UPGRADE),
            (0x80, 0x10, 0, CANCEL_CONSTRUCTION), (0x80, 0x10, 0, BUTTON_ALWAYS),
            (0x80, 0, 0, BUTTON_ALWAYS), (0, 0x10, 0, BUTTON_ALWAYS)]:
        u = unit(emu, flags=flags, sflags=sflags, type=type_)
        _u32(emu, STATUS_UNIT, 0, u)
        set_selection(emu, [u])       # the cancel gates read the selection
        b = button(emu, available=avail)
        diffs = cemu.run_pair(emu, 0x28434, cm, "ButtonAvailable_", b,
                              watch=[(explicit, 4), (SELECTION_INDEX, 2)], out_regs=("eax",))
        assert diffs == [], (hex(flags), hex(sflags), hex(type_), hex(avail), diffs)


def test_t4_status_panel_press_update():
    """0x28580 StatusPanelPressUpdate: a point inside/outside the focused rect
    arms/disarms the button, redraws it and unions the rect."""
    emu = Emu()
    cm = load(emu, "input_reference.c")
    drawn = stub_call(emu, BUTTON_DRAW, 2)
    unioned = stub_call(emu, DIRTY_RECT_UNION, 1)
    r = rect(emu, 2, 0x74, 0x21, 0x8a)
    b = button(emu)
    pt = emu.alloc(8)
    for x, y, pressed in [(10, 0x7A, 0), (10, 0x7A, 1), (1, 0x7A, 1), (10, 0x90, 0),
                          (2, 0x74, 1), (0x21, 0x8a, 0)]:
        _u32(emu, STATUS_BUTTON, 0, b)
        _u32(emu, STATUS_BUTTON_RECT, 0, r)
        _u16(emu, STATUS_PRESSED, 0, pressed)
        emu.write(pt, struct.pack("<4h", 0, 0, x, y))
        diffs = cemu.run_pair(emu, 0x28580, cm, "StatusPanelPressUpdate_", pt,
                              watch=[(STATUS_PRESSED, 2), (drawn, 8), (unioned, 4),
                                     (CUR_BITMAP, 4)], out_regs=())
        assert diffs == [], (x, hex(y), pressed, diffs)


def test_t4_status_panel_lock_adjust():
    """0x29424 StatusPanelLockAdjust: the counting, the zero floor and the
    "no pending network event" gate."""
    emu = Emu()
    cm = load(emu, "panel_lock_adjust.c")
    for lock, on, pending in [(0, 1, 0), (0, 0, 0), (3, 0, 0), (0xFFFF, 1, 0),
                              (5, 1, 1), (5, 0, 1), (0, 1, 1)]:
        _u16(emu, STATUS_LOCK, 0, lock)
        _u16(emu, PLAYER_SLOT, 0, pending)
        diffs = cemu.run_pair(emu, 0x29424, cm, "StatusPanelLockAdjust_", on,
                              watch=[(STATUS_LOCK, 2)], out_regs=())
        assert diffs == [], (lock, on, pending, diffs)


def test_t4_status_panel_lock_clear():
    """0x29410 StatusPanelLockClear: the lock word is zeroed."""
    emu = Emu()
    cm = load(emu, "panel_lock_clear.c")
    for lock in (0, 1, 0x1234):
        _u16(emu, STATUS_LOCK, 0, lock)
        diffs = cemu.run_pair(emu, 0x29410, cm, "StatusPanelLockClear_",
                              watch=[(STATUS_LOCK, 2)], out_regs=())
        assert diffs == [], (lock, diffs)


def test_t4_status_panel_set_unit():
    """0x290f8 StatusPanelSetUnit: hide the panel (and restore the input) only
    when it is showing, then store the requested unit."""
    emu = Emu()
    cm = load(emu, "init_reference.c")
    restored = stub_call(emu, MAP_INPUT_RESTORE, 0)
    u = unit(emu, type=0)
    for visible in (0, 1, 2):
        _u16(emu, STATUS_VISIBLE, 0, visible)
        _u32(emu, STATUS_UNIT_REQ, 0, 0)
        diffs = cemu.run_pair(emu, 0x290F8, cm, "StatusPanelSetUnit_", u,
                              watch=[(STATUS_VISIBLE, 2), (STATUS_UNIT_REQ, 4)], out_regs=())
        assert diffs == [], (visible, diffs)


def test_t4_status_text_for_unit():
    """0x28d58 StatusTextForUnit: the carrying texts, the training/research texts
    of a busy building and the repair cost, with sprintf modelled."""
    emu = Emu()
    cm = load(emu, "panel_text_reference.c")
    stub_sprintf(emu)
    watch = [(STATUS_TEXT, 4), (STATUS_TEXT_PROD, 0x54), (STATUS_TEXT_REPAIR, 0x14)]
    cases = [unit(emu, type=2, state=0x20), unit(emu, type=3, state=0xA0),
             unit(emu, type=0), unit(emu, type=0, owner=1),
             unit(emu, type=0x20, sflags=0x10, order=0x0F, prod_type=0),
             unit(emu, type=0x20, sflags=0x10, order=0x0F, prod_type=0x35),
             unit(emu, type=0x20, sflags=0x10, order=0x10, prod_type=0),
             unit(emu, type=0x20, hp=30), unit(emu, type=0x20, hp=59),
             unit(emu, type=2, hp=1)]
    for u in cases:
        _u32(emu, STATUS_UNIT, 0, u)
        diffs = cemu.run_pair(emu, 0x28D58, cm, "StatusTextForUnit_",
                              watch=watch, out_regs=())
        assert diffs == [], (emu.read(u, UNIT_SIZE).hex(), diffs)


def test_t4_gold_mine_panel_draw():
    """0x2839c GoldMinePanelDraw: the 'gold left' line with several amounts."""
    emu = Emu()
    cm = load(emu, "panel_text_reference.c")
    stub_sprintf(emu)
    color = stub_call(emu, TEXT_SET_COLOR_BASE, 1)
    text = stub_text(emu)
    for gold in (0, 1, 0x7FFF, 0x12345678):
        u = unit(emu, type=0x32, target=gold)
        _u32(emu, STATUS_UNIT, 0, u)
        diffs = cemu.run_pair(emu, 0x2839C, cm, "GoldMinePanelDraw_",
                              watch=[(color, 4), (text, 0x30), (0x5ACF0, 4)], out_regs=())
        assert diffs == [], (gold, diffs)


def test_t4_status_panel_handle_key():
    """0x29354 StatusPanelHandleKey: F10 opens the menu, the card's scan codes
    run their actions, the lock and the foreign-owner gate."""
    emu = Emu()
    cm = load(emu, "input_reference.c")
    menu = stub_call(emu, NET_SEND_CONTROL, 1)
    act = stub_call(emu, ACTION_MOVE, 1)
    u = unit(emu, type=0, owner=0)
    _u32(emu, STATUS_UNIT, 0, u)
    _u32(emu, STATUS_BUTTON, 0, button(emu))
    evt = emu.alloc(16)
    for key, unit_type, lock, owner in [(0x44, 0, 0, 0), (0x32, 0, 0, 0),
                                        (0x32, 0, 1, 0), (0x32, 0, 0, 1),
                                        (0x1E, 0, 0, 0), (0x99, 0, 0, 0),
                                        (0x44, 0xFFFF, 0, 0), (0x32, 0x33, 0, 0)]:
        _u16(emu, PLAYER_SLOT, 0, 0)
        _u16(emu, STATUS_LOCK, 0, lock)
        _u16(emu, STATUS_UNIT_TYPE, 0, unit_type)
        u2 = unit(emu, type=0, owner=owner)
        _u32(emu, STATUS_UNIT, 0, u2)
        emu.write(evt, struct.pack("<4H", 0, 0, 0, 0) + struct.pack("<2H", 0, key))
        diffs = cemu.run_pair(emu, 0x29354, cm, "StatusPanelHandleKey_", evt,
                              watch=[(menu, 4), (act, 4)], out_regs=())
        assert diffs == [], (hex(key), hex(unit_type), lock, owner, diffs)
        emu.write(evt, struct.pack("<4H", 0, 0, 0, 0) + struct.pack("<2H", 0, key))
        orig_ret = emu.call(0x29354, evt) & 0xFFFF
        emu.write(evt, struct.pack("<4H", 0, 0, 0, 0) + struct.pack("<2H", 0, key))
        c_ret = cm.call("StatusPanelHandleKey_", evt) & 0xFFFF
        assert orig_ret == c_ret, (hex(key), hex(unit_type), lock, owner, orig_ret, c_ret)


def test_t4_farm_panel_draw():
    """0x28298 FarmPanelDraw: the two 'food usage' lines, the red colour when the
    player is over the cap, and the caches it leaves behind."""
    emu = Emu()
    cm = load(emu, "panel_text_reference.c")
    stub_sprintf(emu)
    color = stub_call(emu, TEXT_SET_COLOR_BASE, 1)
    text = stub_text(emu)
    for men, summ, food in [(4, 0, 16), (16, 0, 8), (0, 0, 0), (0xFFFF, 1, 4)]:
        _u16(emu, PLAYER_MEN, 0, men)
        _u16(emu, PLAYER_SUMMONED, 0, summ)
        _u16(emu, PLAYER_FOOD, 0, food)
        _u16(emu, STATUS_MEN_USED, 0, 0)
        _u16(emu, STATUS_MEN_GROWN, 0, 0)
        diffs = cemu.run_pair(emu, 0x28298, cm, "FarmPanelDraw_",
                              watch=[(STATUS_MEN_USED, 2), (STATUS_MEN_GROWN, 2),
                                     (color, 4), (text, 0x30), (0x5ACF0, 4)],
                              out_regs=())
        assert diffs == [], (men, summ, food, diffs)


def test_t4_can_cancel_training():
    """0x28170 CanCancelTraining: the busy flag, the 'no progress yet' test and
    the produced-type menu id; the selected unit is the one the gate reads."""
    emu = Emu()
    cm = load(emu, "can_cancel_training.c")
    for sflags, progress, prod in [(0, 0, 0), (0x10, 0, 0), (0x10, 1, 0),
                                   (0x10, 0, 0x35), (0x10, 0, 0x36), (0x10, 0, 0x1F)]:
        u = unit(emu, sflags=sflags, progress=progress, prod_type=prod)
        set_selection(emu, [u])
        diffs = cemu.run_pair(emu, 0x28170, cm, "CanCancelTraining_", 0,
                              watch=[(SELECTION_INDEX, 2)], out_regs=("eax",))
        assert diffs == [], (hex(sflags), progress, hex(prod), diffs)


def test_t4_can_cancel_construction():
    """0x281ac CanCancelConstruction: the same tests with the == 0x35 sense."""
    emu = Emu()
    cm = load(emu, "can_cancel_construction.c")
    for sflags, progress, prod in [(0, 0, 0x35), (0x10, 0, 0x35), (0x10, 1, 0x35),
                                   (0x10, 0, 0), (0x10, 0, 0x36)]:
        u = unit(emu, sflags=sflags, progress=progress, prod_type=prod)
        set_selection(emu, [u])
        diffs = cemu.run_pair(emu, 0x281AC, cm, "CanCancelConstruction_", 0,
                              watch=[(SELECTION_INDEX, 2)], out_regs=("eax",))
        assert diffs == [], (hex(sflags), progress, hex(prod), diffs)


def test_t4_can_build_basic_structure():
    """0x280b8 CanBuildBasicStructure: the one-unit gate and the three mask
    bits (farm/lumber mill/barracks)."""
    emu = Emu()
    cm = load(emu, "can_build_basic.c")
    for count, mask in [(0, 0xFFFFFFFF), (1, 0), (1, 0x80), (1, 0x1000), (1, 0x100),
                        (1, 0x1000000), (2, 0x80), (1, 0x1080)]:
        _u16(emu, SELECTION_COUNT, 0, count)
        _u32(emu, SCENARIO_UNIT_MASK, 0, mask)
        diffs = cemu.run_pair(emu, 0x280B8, cm, "CanBuildBasicStructure_", 1,
                              watch=[(SCENARIO_UNIT_MASK, 4)], out_regs=("eax",))
        assert diffs == [], (count, hex(mask), diffs)


def test_t4_can_build_advanced_structure():
    """0x280e8 CanBuildAdvancedStructure: the five prerequisite tests (blacksmith,
    church, stable, tower, town hall rebuild)."""
    emu = Emu()
    cm = load(emu, "can_build_advanced.c")
    for count, mask, mill, smith, stable, hall in [
            (0, 0xFFFFFFFF, 1, 1, 1, 0), (1, 0, 1, 1, 1, 0),
            (1, 0x4000, 1, 0, 0, 1), (1, 0x4000, 0, 1, 0, 1),
            (1, 0x200, 1, 0, 0, 1), (1, 0x400, 0, 1, 0, 1),
            (1, 0x2000, 1, 0, 0, 1), (1, 0x800, 0, 0, 0, 1),
            (1, 0x800, 0, 0, 0, 0), (1, 0xFFFFFFFF, 0, 0, 0, 0)]:
        _u16(emu, SELECTION_COUNT, 0, count)
        _u32(emu, SCENARIO_UNIT_MASK, 0, mask)
        _u16(emu, 0x58E0A, 0, mill)
        _u16(emu, 0x58E14, 0, smith)
        _u16(emu, 0x58E3C, 0, stable)
        _u32(emu, 0x58DB0, 0, hall)
        diffs = cemu.run_pair(emu, 0x280E8, cm, "CanBuildAdvancedStructure_", 1,
                              watch=[(SCENARIO_UNIT_MASK, 4), (0x58DB0, 4)],
                              out_regs=("eax",))
        assert diffs == [], (count, hex(mask), mill, smith, stable, hall, diffs)


# ---------------------------------------------------------------------------
# T4 (second batch): the panel's painters, life cycle, input side and update.
# The five reference functions of src/status/{draw,input,update}_reference.c
# plus text_refresh_reference.c (the info line takes the packed cursor point,
# not two shorts).  Every callee with graphics/resource side effects is a stub
# so the test compares the function's own logic: argument order, call order and
# the state it writes.
# ---------------------------------------------------------------------------
STATUS_EVENT_CALLBACK = 0x59424
STATUS_MOUSE_CB = 0x5940C
STATUS_FRAME_CB = 0x59414
STATUS_CLICK_CB = 0x5941C
STATUS_MEN_D2 = 0x5A2D2
CUR_FONT = 0x5ACF0
SCENARIO_RACE = 0x50088
STATUS_HELP_KIND = 0x5A420
STATUS_HELP_GOLD = 0x5A422
STATUS_HELP_LUMBER = 0x5A424
STATUS_WORK_STATE = 0x5A2E2
STATUS_PANEL_BM = 0x53568
STATUS_PANEL_RECT = 0x53570
UNIT_ICON_GRP = 0x53560
UNIT_PORTRAIT_GRP = 0x53564
STATUS_BAR_ICON_BM = 0x53520
STATUS_PANEL_ART = 0x53548
STATUS_INFO_BM_NORMAL = 0x53528
STATUS_INFO_BM_PRESSED = 0x53530
STATUS_BUTTON_BM_NORMAL = 0x53538
STATUS_BUTTON_BM_PRESSED = 0x53540
STATUS_CARRY_BM = 0x53550
BITMAPS = 0x53520                       # the ten Bitmap headers 0x53520..0x53570
BUTTON_AVAILABLE = 0x28434
SET_HELP_TEXT = 0x19F80
SET_CURSOR = 0x13DD0
LAYER_ADD = 0x21D0C
LAYER_INVALIDATE = 0x31F70
RESOURCE_BEGIN = 0x31870
RESOURCE_READ = 0x32740
RESOURCE_READ_HEADER_BODY = 0x323E0
RESEARCH_COST = 0x28C60
STATUS_PANEL_CACHE = 0x287F0
STATUS_PANEL_DRAW = 0x28894
UNIT_PANEL_DRAW = 0x28824
STATUS_TEXT_FOR_UNIT = 0x28D58
HEALTH_BAR_DRAW = 0x2864C
HEALTH_BAR_DRAW_SINGLE = 0x28700
PROGRESS_BAR_DRAW = 0x28770
DIRTY_RECT_SAVE = 0x5ACD0               # dirty_x1 .. dirty_h (12 bytes)


def stub_value(emu, addr, nargs, size=0x20):
    """stub_call plus a return value: the test writes the dword and the stub
    returns it, so both the original and the C see the same answer."""
    rec = stub_call(emu, addr, nargs, size)
    ctl = emu.alloc(4)
    _u32(emu, ctl, 0, 0)
    inner = emu.stubs[addr]

    def fn(e):
        inner(e)
        return e.u32(ctl)

    emu.stubs[addr] = fn
    return rec, ctl


def panel_entry(emu, index, nbuttons, buttons, changed=0, draw=0):
    """Write a UnitPanel record into unit_panel_table[index] (14-byte stride)."""
    a = UNIT_PANEL_TABLE + 14 * index
    _u16(emu, a, 0, nbuttons)
    _u32(emu, a, 2, buttons)
    _u32(emu, a, 6, changed)
    _u32(emu, a, 0xA, draw)
    return a


def stub_at(emu, nargs=0, size=0x20):
    """A recorder at a fresh heap address (for indirect callbacks)."""
    addr = emu.alloc(16)
    rec = stub_call(emu, addr, nargs, size)
    return addr, rec


def test_t4_button_draw():
    """0x284a8 ButtonDraw: the info-line pseudo button, the normal/pressed
    background, the icon frame and the +2/+3 offset; the bitmap callees are
    recorders (their x/y/source arguments are the whole logic)."""
    emu = Emu()
    cm = load(emu, "button_draw_reference.c")
    avail, avail_ctl = stub_value(emu, BUTTON_AVAILABLE, 1)
    blit = stub_call(emu, BITMAP_BLIT, 4)
    blit_all = stub_call(emu, BITMAP_BLIT_ALL, 2)      # src is &icon on each stack
    grp = stub_call(emu, GRP_FRAME_BITMAP, 2)          # the out bitmap differs
    watch = [(avail, 4), (blit, 16), (blit_all, 8), (grp, 8)]
    for b, what in [(STATUS_INFO_BUTTON, "info"),
                    (button(emu, icon=0), "icon0"),
                    (button(emu, icon=5, face=0x33), "icon5")]:
        for pressed in (0, 1):
            for allowed in (0, 1):
                _u32(emu, avail_ctl, 0, allowed)
                diffs = cemu.run_pair(emu, 0x284A8, cm, "ButtonDraw_", b, pressed,
                                      watch=watch, out_regs=())
                assert diffs == [], (what, pressed, allowed, diffs)


def test_t4_status_panel_click():
    """0x28600 StatusPanelClick: press update, input restore, hide, and the
    armed button's redraw + action; every callee is a recorder."""
    emu = Emu()
    cm = load(emu, "status_panel_click_reference.c")
    press = stub_call(emu, 0x28580, 1)
    restore = stub_call(emu, MAP_INPUT_RESTORE, 0)
    draw = stub_call(emu, BUTTON_DRAW, 2)
    union = stub_call(emu, DIRTY_RECT_UNION, 1)
    screen = stub_call(emu, SCREEN_UPDATE, 0)
    act = stub_call(emu, ACTION_MOVE, 1)
    watch = [(STATUS_VISIBLE, 2), (press, 4), (restore, 4), (draw, 8),
             (union, 4), (screen, 4), (act, 4)]
    pt = emu.alloc(8)
    emu.write(pt, struct.pack("<4h", 0, 0, 10, 0x7A))
    b = button(emu, action=ACTION_MOVE, arg=7)
    r = rect(emu, 2, 0x74, 0x21, 0x8A)
    for pressed in (0, 1):
        for visible in (0, 1):
            _u16(emu, STATUS_VISIBLE, 0, visible)
            _u16(emu, STATUS_PRESSED, 0, pressed)
            _u32(emu, STATUS_BUTTON, 0, b)
            _u32(emu, STATUS_BUTTON_RECT, 0, r)
            diffs = cemu.run_pair(emu, 0x28600, cm, "StatusPanelClick_", pt,
                                  watch=watch, out_regs=())
            assert diffs == [], (pressed, visible, diffs)


def test_t4_status_panel_show():
    """0x2905c StatusPanelShow: the lock/button gates, the four callback slots
    (0x5940c/0x59414/0x5941c/0x59424), the cursor, and the armed flag from the
    point being inside or outside the focused rect."""
    emu = Emu()
    cm = load(emu, "status_panel_show_reference.c")
    press = stub_call(emu, 0x28580, 1)
    cursor = stub_call(emu, SET_CURSOR, 1)
    watch = [(STATUS_FRAME_CB, 4), (STATUS_CLICK_CB, 4), (STATUS_MOUSE_CB, 4),
             (STATUS_EVENT_CALLBACK, 4), (STATUS_VISIBLE, 2), (STATUS_PRESSED, 2),
             (press, 4), (cursor, 4)]
    r = rect(emu, 2, 0x74, 0x21, 0x8A)
    pt = emu.alloc(8)
    b = button(emu)
    for lock in (0, 1, 5):
        for has_button in (0, 1):
            for x, y in [(10, 0x7A), (1, 0x7A), (10, 0x90), (0x22, 0x7A)]:
                _u16(emu, STATUS_LOCK, 0, lock)
                _u32(emu, STATUS_BUTTON, 0, b if has_button else 0)
                _u32(emu, STATUS_BUTTON_RECT, 0, r)
                _u16(emu, STATUS_VISIBLE, 0, 0)
                _u16(emu, STATUS_PRESSED, 0, 0)
                emu.write(pt, struct.pack("<4h", 0, 0, x, y))
                diffs = cemu.run_pair(emu, 0x2905C, cm, "StatusPanelShow_", pt,
                                      watch=watch, out_regs=())
                assert diffs == [], (lock, has_button, x, hex(y), diffs)


def test_t4_status_panel_init():
    """0x29120 StatusPanelInit: the resource ids it asks for (0x16b, 0x169/0x16a
    by race, 0x16c..0x16f, 0x19a/0x19b, 0xe4+race, 0x19c), where it stores the
    two grps, the layer add and the artwork blit; the resource layer is
    stubbed."""
    emu = Emu()
    cm = load(emu, "status_panel_init.c")
    begin = stub_call(emu, RESOURCE_BEGIN, 2)
    read = stub_value(emu, RESOURCE_READ, 2)
    body = stub_call(emu, RESOURCE_READ_HEADER_BODY, 2)
    layer = stub_call(emu, LAYER_ADD, 4)       # 5th argument is pushed
    blit = stub_call(emu, BITMAP_BLIT_ALL, 3)
    invalidate = stub_call(emu, LAYER_INVALIDATE, 1)
    emu.stub_pops[LAYER_ADD] = 4               # the watcall callee pops it
    watch = [(begin, 32), (read[0], 16), (body, 64), (layer, 16), (blit, 12),
             (invalidate, 4), (BITMAPS, 0x50), (STATUS_MEN_D2, 2),
             (STATUS_UNIT_TYPE, 2), (STATUS_LOCK, 2), (STATUS_UNIT, 4),
             (STATUS_UNIT_REQ, 4), (CUR_BITMAP, 4)]
    for race in (0, 1, 2):
        _u16(emu, SCENARIO_RACE, 0, race)
        _u32(emu, read[1], 0, 0x600000 + race)   # ResourceRead's return value
        diffs = cemu.run_pair(emu, 0x29120, cm, "StatusPanelInit_",
                              watch=watch, out_regs=())
        assert diffs == [], (race, diffs)


def test_t4_status_panel_draw():
    """0x28894 StatusPanelDraw: the six panel states (single unit, construction,
    group of 2..4), the type/owner/finished/busy gates, the carry icons and the
    command card call; the painters and the selection iterator are recorders."""
    emu = Emu()
    cm = load(emu, "status_panel_draw.c")
    grp = stub_call(emu, GRP_FRAME_BITMAP, 2)          # out is each side's stack
    blit = stub_call(emu, BITMAP_BLIT_ALL, 2)          # src is &frame
    blit_t = stub_call(emu, BITMAP_BLIT_TRANS, 2)      # src is &frame / a Bitmap
    first = stub_value(emu, SELECTION_FIRST, 0)
    nxt = stub_value(emu, SELECTION_NEXT, 0)
    bar = stub_call(emu, HEALTH_BAR_DRAW, 3)
    bar1 = stub_call(emu, HEALTH_BAR_DRAW_SINGLE, 0)
    prog = stub_call(emu, PROGRESS_BAR_DRAW, 0)
    text = stub_call(emu, DRAW_TEXT, 3)                # the name is fixed data
    color = stub_call(emu, TEXT_SET_COLOR_BASE, 1)
    cache = stub_call(emu, STATUS_PANEL_CACHE, 0)
    card = stub_call(emu, UNIT_PANEL_DRAW, 1)
    watch = [(grp, 8), (blit, 8), (blit_t, 8), (first[0], 4), (nxt[0], 4),
             (bar, 12), (bar1, 4), (prog, 4), (text, 12), (color, 4), (cache, 4),
             (card, 4), (CUR_FONT, 4), (STATUS_WORK_STATE, 1)]
    member = unit(emu, type=0, hp=40)
    _u32(emu, first[1], 0, member)
    _u32(emu, nxt[1], 0, member)
    cases = [
        (None, 0),                                  # no unit at all
        (unit(emu, type=0), 0),
        (unit(emu, type=0, owner=1), 0),
        (unit(emu, type=0), 2),                     # selection of 2 -> state 3
        (unit(emu, type=0), 3),                     # 3 -> state 4
        (unit(emu, type=0), 4),                     # 4 -> state 5
        (unit(emu, type=0), 6),                     # 6 -> state 7
        (unit(emu, type=0x20, flags=0x80, sflags=0x10), 1),  # state 2 (busy)
        (unit(emu, type=0x20, flags=0x80, sflags=0), 1),     # type flag
        (unit(emu, type=0x20, flags=0, sflags=0), 1),        # state 2 (unfinished)
        (unit(emu, type=2, state=0xA0), 1),         # carrying gold
        (unit(emu, type=3, state=0x20), 1),         # carrying lumber
        (unit(emu, type=2, state=0x20), 2),
        (unit(emu, type=0x32, owner=1), 1),         # the gold mine draw
        (unit(emu, type=0x7A), 1),                  # face 0xffff guard
    ]
    for u, count in cases:
        _u32(emu, STATUS_UNIT, 0, u or 0)
        _u16(emu, 0x5A110, 0, count)
        _u16(emu, STATUS_UNIT_TYPE, 0, 0)   # the footman card for UnitPanelDraw
        diffs = cemu.run_pair(emu, 0x28894, cm, "StatusPanelDraw_",
                              watch=watch, out_regs=())
        assert diffs == [], (hex(u or 0), count, diffs)


def test_t4_status_panel_text_refresh():
    """0x28e88 StatusPanelTextRefresh: the packed point in eax (x low word, y
    high word), the info-line hit, the type/owner/empty-card gates and the
    three tooltip kinds (plain, build/train cost, research cost)."""
    emu = Emu()
    cm = load(emu, "status_panel_text_refresh_reference.c")
    statustext = stub_call(emu, STATUS_TEXT_FOR_UNIT, 0)
    help_ = stub_call(emu, SET_HELP_TEXT, 1)
    avail, avail_ctl = stub_value(emu, BUTTON_AVAILABLE, 1)
    research = stub_value(emu, RESEARCH_COST, 2)       # &level is each side's stack
    watch = [(STATUS_BUTTON, 4), (STATUS_BUTTON_RECT, 4), (STATUS_HELP_KIND, 2),
             (STATUS_HELP_GOLD, 2), (STATUS_HELP_LUMBER, 2), (statustext, 4),
             (help_, 4), (avail, 4), (research[0], 8)]
    _u32(emu, research[1], 0, 750)
    buttons = emu.alloc(4 * 0x14)
    b0 = button(emu, icon=0, kind=0, label=0x54D1A, action=0)
    b1 = button(emu, icon=1, kind=1, arg=2, label=0x54D28, action=0)
    b2 = button(emu, icon=2, kind=2, arg=3, label=0x54D30, action=0)
    for i, b in enumerate((b0, b1, b2)):
        emu.write(buttons + 0x14 * i, emu.read(b, 0x14))
    panel_entry(emu, 0x3C, 3, buttons, changed=0, draw=0)
    u = unit(emu, type=0x20, owner=0)
    info = emu.read(STATUS_INFO_RECT, 12)
    x1, y1, x2, y2 = struct.unpack_from("<4h", info)
    inside = ((x1 + x2) // 2) | (((y1 + y2) // 2) << 16)
    r0 = struct.unpack("<6h", emu.read(COMMAND_BUTTON_RECT, 12))
    r1 = struct.unpack("<6h", emu.read(COMMAND_BUTTON_RECT + 12, 12))
    r2 = struct.unpack("<6h", emu.read(COMMAND_BUTTON_RECT + 24, 12))
    cases = [
        (inside, 0x3C, u, 1),                                   # over the info line
        (((r0[0] + r0[2]) // 2) | (((r0[1] + r0[3]) // 2) << 16), 0x3C, u, 1),
        (((r1[0] + r1[2]) // 2) | (((r1[1] + r1[3]) // 2) << 16), 0x3C, u, 1),
        (((r2[0] + r2[2]) // 2) | (((r2[1] + r2[3]) // 2) << 16), 0x3C, u, 1),
        (((r1[0] + r1[2]) // 2) | (((r1[1] + r1[3]) // 2) << 16), 0x3C, u, 0),
        (inside, 0xFFFF, u, 1),                                 # no card
        (inside, 0x3C, unit(emu, type=0x20, owner=1), 1),       # foreign owner
        (3, 0x3C, u, 1),                                        # outside everything
    ]
    for pt, unit_type, who, allowed in cases:
        _u32(emu, STATUS_UNIT, 0, who)
        _u16(emu, STATUS_UNIT_TYPE, 0, unit_type)
        _u32(emu, avail_ctl, 0, allowed)
        diffs = cemu.run_pair(emu, 0x28E88, cm, "StatusPanelTextRefresh_", pt,
                              watch=watch, out_regs=())
        assert diffs == [], (hex(pt), hex(unit_type), allowed, diffs)


def test_t4_unit_panel_update():
    """0x29450 UnitPanelUpdate: the lock gate, the "nothing changed" early
    outs (card callback, selection count, dirty flag), the artwork repaint with
    the dirty-rect save/restore, the adopted unit/type and the visible-panel
    teardown; the painters and the input restore are recorders."""
    emu = Emu()
    cm = load(emu, "unit_panel_update_reference.c")
    changed, changed_rec = stub_at(emu, 0)
    blit = stub_call(emu, BITMAP_BLIT_ALL, 3)          # src is fixed artwork
    box = stub_call(emu, DIRTY_RECT_ADD_BOX, 4)
    cache = stub_call(emu, STATUS_PANEL_CACHE, 0)
    avail, avail_ctl = stub_value(emu, BUTTON_AVAILABLE, 1)
    restore = stub_call(emu, MAP_INPUT_RESTORE, 0)
    statustext = stub_call(emu, STATUS_TEXT_FOR_UNIT, 0)
    panel_draw = stub_call(emu, STATUS_PANEL_DRAW, 0)
    screen = stub_call(emu, SCREEN_UPDATE, 0)
    watch = [(DIRTY_RECT_SAVE, 12), (STATUS_SEL_COUNT, 2), (STATUS_UNIT, 4),
             (STATUS_UNIT_TYPE, 2), (STATUS_VISIBLE, 2), (STATUS_DIRTY, 2),
             (CUR_BITMAP, 4), (changed_rec, 4), (blit, 12), (box, 16), (cache, 4),
             (avail, 4), (restore, 4), (statustext, 4), (panel_draw, 4),
             (screen, 4)]
    panel_entry(emu, 0x3C, 0, 0, changed=changed, draw=0)
    u_a = unit(emu, type=0x20, type_copy=0x3C, hp=30)
    u_b = unit(emu, type=0x21, type_copy=0x3C, hp=20)
    cases = [
        # lock, req, shown, dirty, sel_count, player_count, changed, visible, avail
        (1, u_a, u_a, 1, 0, 0, 0, 0, 1),
        (0, 0, 0, 0, 0, 0, 0, 0, 1),
        (0, u_a, u_a, 0, 0, 0, 0, 0, 1),          # nothing changed
        (0, u_a, u_a, 1, 0, 0, 0, 0, 1),          # dirty -> redraw
        (0, u_a, u_a, 0, 0, 0, 1, 0, 1),          # card callback -> redraw
        (0, u_a, u_a, 0, 1, 0, 0, 0, 1),          # selection count -> redraw
        (0, u_a, u_b, 0, 0, 0, 0, 0, 1),          # different unit -> redraw
        (0, 0, u_b, 0, 0, 0, 0, 0, 1),            # cleared selection -> redraw
        (0, u_a, u_a, 1, 0, 0, 0, 1, 1),          # visible, type unchanged
        (0, u_a, u_b, 0, 0, 0, 0, 1, 1),          # visible, type changed
        (0, u_a, u_b, 0, 0, 0, 0, 1, 0),          # visible, button unavailable
        (0, u_a, u_b, 0, 0, 0, 0, 1, 1),
    ]
    for lock, req, shown, dirty, sel_count, player_count, ch, visible, allowed in cases:
        _u16(emu, STATUS_LOCK, 0, lock)
        _u32(emu, STATUS_UNIT_REQ, 0, req or 0)
        _u32(emu, STATUS_UNIT, 0, shown or 0)
        _u16(emu, STATUS_DIRTY, 0, dirty)
        _u16(emu, STATUS_SEL_COUNT, 0, sel_count)
        _u16(emu, SELECTION_COUNT, 0, player_count)
        _u16(emu, STATUS_UNIT_TYPE, 0, 0x20)
        _u16(emu, STATUS_VISIBLE, 0, visible)
        _u32(emu, STATUS_BUTTON, 0, button(emu))
        _u32(emu, STATUS_BUTTON_RECT, 0, rect(emu, 2, 0x74, 0x21, 0x8A))
        _u32(emu, changed_rec, 0, ch)
        _u32(emu, avail_ctl, 0, allowed)
        # the dirty rect the function must save and restore
        emu.write(DIRTY_RECT_SAVE, struct.pack("<6h", 1, 2, 3, 4, 2, 2))
        diffs = cemu.run_pair(emu, 0x29450, cm, "UnitPanelUpdate_",
                              watch=watch, out_regs=())
        assert diffs == [], (lock, hex(req or 0), hex(shown or 0), dirty, diffs)
