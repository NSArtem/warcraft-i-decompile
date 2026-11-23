"""Tests for the mod_16390 area (war.exe 0x16390..0x19020).

The range holds three objects' worth of code (analysis/modules.toml's boundary
is the linker padding, the strings are a pool-slice heuristic):

  * DLGS.C, the modal dialog engine 0x16390..0x1825c: descriptor resources,
    0x1c-byte item lists, list/prev-next/edit controls and the two modal loops;
  * the UI event layer 0x182e4..0x1878c the dialogs and menus dispatch
    through (UiInputInit 0x18488 / UiEventPump 0x184cc are named in
    playflic.toml, the rest here);
  * the victory epilogue 0x18790..0x19013 (finale FLIC + 'The End' credits).

Names/evidence: analysis/symbols/mod_16390.toml; prose:
docs/subsystems/mod_16390.md.

Kinds of test here:
  * T3 re-check of the byte-matched C files under `wc1.match` (Watcom 10.0a);
  * a guard that the reference files stay near misses (their logic is right,
    the register allocation differs) - promoting one means updating the TOML;
  * T4 difftests: the original list-control functions run under wc1.emu next
    to the compiled reference C on the same fake dialog (cemu.run_pair);
  * structural invariants: every discovered function of the range is named,
    the module field matches analysis/modules.toml, the string and event
    handler tables the engine reads are what the TOML claims.
"""
import os
import struct

import pytest

from wc1 import analysis, cemu, match, path, symbols, t4spec

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "mod_16390")

# --------------------------------------------------------------- addresses
DIALOG_ART_BM = 0x593E0
DIALOG_ART_DATA = 0x593E4
EDIT_BUFFER = 0x593E8
EDIT_CURSOR = 0x593EC
AUTO_REPEAT = 0x593EE
MOUSE_IN_PREVIEW = 0x593F0
DIALOG_RESULT = 0x593F2
DIALOG_SOUNDS = 0x593F4
LAST_KEY = 0x593F8
DIALOG_RUNNING = 0x593FA
LEFT_HELD = 0x593FC
EVENT_HANDLERS = 0x59400
DIALOG_LEFT_PRESS = 0x59410
DIALOG_RIGHT_PRESS = 0x59418
DIALOG_IDLE = 0x59420
EVENT_PRE = 0x59424
UI_MOUSE_X = 0x59428
UI_MOUSE_Y = 0x5942A
UI_NET_FORWARD = 0x5942C
UI_BUTTON_BITS = 0x5942E
OUTRO_DONE = 0x59430
OUTRO_IS_ORC = 0x59432
OUTRO_FRAME = 0x59434
OUTRO_TICK = 0x59436
EVENT_TABLE = 0x51770
STR_EMPTY_SLOT = 0x56BD8
STR_THE_END = 0x56BE8
CURSOR_HOTSPOT_X = 0x5AA60
CURSOR_HOTSPOT_Y = 0x5AA62
CURSOR_LAYER_ID = 0x5AA78
LAYERS = 0x5AA90
LAYER_SIZE = 18
ALT_FONT = 0x59220

# the 21 T3 files (byte-identical under Watcom 10.0a)
BUILT = [
    "edit_default_char_filter.c",
    "dialog_load.c",
    "dialog_call_open.c",
    "dialog_call_close.c",
    "dialog_call_select.c",
    "dialog_check_done.c",
    "dialog_free.c",
    "dialog_preview_cursor.c",
    "dialog_idle_handler.c",
    "dialog_left_press_handler.c",
    "dialog_left_release_handler.c",
    "dialog_sounds_load.c",
    "dialog_sounds_free.c",
    "dialog_art_load.c",
    "dialog_art_free.c",
    "no_op.c",
    "ui_mouse_move.c",
    "outro_tick.c",
    "outro_end.c",
    "outro_draw_line.c",
    "outro_show_frame.c",
    "outro_play.c",
]
# the reference C (logic reconstructed, not byte-identical: see t3_blocker)
REFS = [
    "list_selected_text_reference.c",
    "list_sel_prev_reference.c",
    "list_sel_next_reference.c",
    "dialog_hit_test_reference.c",
    "dialog_key_handler_reference.c",
    "outro_draw_text_page_reference.c",
    "ui_button_press_reference.c",
    "ui_button_release_reference.c",
    "ui_frame_reference.c",
    "list_select_at_mouse_reference.c",
]


@pytest.fixture(scope="module")
def prog():
    return analysis.run()


def _flags(src):
    return match.file_cflags(src)


def _compiled(src):
    out = path("build", "mod_16390", "t_" + os.path.splitext(os.path.basename(src))[0] + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    return match.compile_c(src, _flags(src), out)


def _load(emu, name):
    # the reference C only needs this object's own symbols; nothing else
    return cemu.load(emu, os.path.join(AREA, name))


# ---------------------------------------------------------------- T3 / near miss

@pytest.mark.parametrize("name", BUILT)
def test_built_c_matches(prog, name):
    """Every function in a built file is byte-identical (T3, Watcom 10.0a)."""
    mod = _compiled(os.path.join(AREA, name))
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    assert res, name
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, bad


@pytest.mark.parametrize("name", REFS)
def test_reference_c_stays_a_near_miss(prog, name):
    """The reference files model the logic but are not byte-matches; if one
    starts matching it has to be promoted into the built set with `match:`
    evidence."""
    mod = _compiled(os.path.join(AREA, name))
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    t4spec.assert_ref_results(os.path.join(AREA, name), res, name)


# ---------------------------------------------------------------- T4 difftests
#
# The list-control trio takes a Dialog (d[0] = layer, d[6] = int *params) and a
# 0x1c-byte DialogItem (item[0x12] = text table / row count, item[0x16] = the
# parameter index, item[2] = flags).  The tests build that state with
# emu.alloc (zeroed scratch) and compare the original with the compiled C.

def _dialog(emu):
    d = emu.alloc(0x40)
    item = emu.alloc(0x40)
    params = emu.alloc(0x40)
    texts = emu.alloc(0x40)
    strs = emu.alloc(0x80)
    return d, item, params, texts, strs


def _put_u16(emu, a, v):
    emu.write(a, struct.pack("<H", v & 0xFFFF))


def _put_u32(emu, a, v):
    emu.write(a, struct.pack("<I", v & 0xFFFFFFFF))


def _get_u32(emu, a):
    return struct.unpack("<I", emu.read(a, 4))[0]


def test_t4_list_selected_text():
    """0x163a8 ListSelectedText: the selection word at params[item->id] picks
    the item's string; out-of-range selections are *not* clamped (the caller
    keeps them in range), so probe 0..3 rows and both parameter slots."""
    emu = Emu()
    cm = _load(emu, "list_selected_text_reference.c")
    d, item, params, texts, strs = _dialog(emu)
    rows = [strs, strs + 0x20, strs + 0x40, strs + 0x60]
    for k in range(4):
        _put_u32(emu, texts + 4 * k, rows[k])
        emu.write(rows[k], b"row%d\0" % k)
    _put_u32(emu, d + 6, params)
    for slot in (0, 1, 2):
        _put_u16(emu, item + 0x16, slot)
        _put_u32(emu, item + 0x12, texts)
        for sel in (0, 1, 2, 3):
            # the word the original reads is the low half of the dword
            _put_u32(emu, params + 4 * slot, sel)
            diffs = cemu.run_pair(emu, 0x163A8, cm, "ListSelectedText_",
                                  d, item, out_regs=("eax",))
            assert diffs == [], (slot, sel, diffs)


def test_t4_list_sel_prev():
    """0x17430 ListSelPrev: decrement, and the flag-bit-0 wrap to count-1."""
    emu = Emu()
    cm = _load(emu, "list_sel_prev_reference.c")
    d, item, params, _texts, _strs = _dialog(emu)
    _put_u32(emu, d + 6, params)
    for slot in (0, 1):
        _put_u16(emu, item + 0x16, slot)
        for count in (0, 1, 5):
            _put_u32(emu, item + 0x12, count)
            for flags in (0, 1, 3):
                _put_u16(emu, item + 2, flags)
                for sel in (0, 1, 4):
                    _put_u32(emu, params + 4 * slot, sel)
                    diffs = cemu.run_pair(emu, 0x17430, cm, "ListSelPrev_",
                                          d, item, watch=[(params + 4 * slot, 4)],
                                          out_regs=())
                    assert diffs == [], (slot, count, flags, sel, diffs)


def test_t4_list_sel_next():
    """0x1746c ListSelNext: increment, and the flag-bit-0 wrap to 0."""
    emu = Emu()
    cm = _load(emu, "list_sel_next_reference.c")
    d, item, params, _texts, _strs = _dialog(emu)
    _put_u32(emu, d + 6, params)
    for slot in (0, 1):
        _put_u16(emu, item + 0x16, slot)
        for count in (0, 1, 5):
            _put_u32(emu, item + 0x12, count)
            for flags in (0, 1, 3):
                _put_u16(emu, item + 2, flags)
                for sel in (0, 3, 4):
                    _put_u32(emu, params + 4 * slot, sel)
                    diffs = cemu.run_pair(emu, 0x1746C, cm, "ListSelNext_",
                                          d, item, watch=[(params + 4 * slot, 4)],
                                          out_regs=())
                    assert diffs == [], (slot, count, flags, sel, diffs)


# ---------------------------------------------------------------- structure

def _named(prog):
    funcs, datas, _ = symbols.load()
    by = {a: e for a, e in funcs.items()}
    mine = {a: e for a, e in by.items()
            if e.get("_file", "").endswith("mod_16390.toml")}
    return by, mine


def test_every_range_function_is_named(prog):
    """All 54 discovered starts in 0x16390..0x19020 have a symbol entry (two of
    them belong to playflic.toml)."""
    by, _mine = _named(prog)
    starts = [f["start"] for f in prog.functions if 0x16390 <= f["start"] < 0x19020]
    assert len(starts) == 54
    missing = [hex(a) for a in starts if a not in by]
    assert not missing, missing


def test_entries_are_in_this_module(prog):
    _by, mine = _named(prog)
    assert len(mine) == 52
    for a, e in mine.items():
        assert e.get("module") == "mod_16390", (hex(a), e.get("module"))


def test_module_range(prog):
    """The area is the modules.toml range mod_16390 (0x16390..0x19020) and its
    neighbours are the setup menu and the FLIC decoder."""
    starts = sorted(f["start"] for f in prog.functions if 0x16390 <= f["start"] < 0x19020)
    assert starts[0] == 0x16390
    assert starts[-1] == 0x18FB0
    # the first function after the range belongs to the next module
    nxt = min(f["start"] for f in prog.functions if f["start"] >= 0x19020)
    assert nxt < 0x19470


def test_strings_the_engine_reads(prog):
    _by, _mine = _named(prog)
    funcs, datas, _ = symbols.load()

    def cstr(addr, n):
        img = prog.image[2]
        return bytes(img[addr - 0x50000:addr - 0x50000 + n])

    assert datas[STR_EMPTY_SLOT]["name"] == "str_empty_slot"
    assert cstr(STR_EMPTY_SLOT, 13) == b"[empty slot]\0"
    assert datas[STR_THE_END]["name"] == "str_the_end"
    assert cstr(STR_THE_END, 8) == b"The End\0"


def test_event_handler_table(prog):
    """0x51770 holds the ten dispatchers indexed by the event sub code; the
    dialog and UI entries of this area are the ones documented in the TOML."""
    img = prog.image[2]
    table = [struct.unpack("<I", bytes(img[EVENT_TABLE - 0x50000 + 4 * k:
                                          EVENT_TABLE - 0x50000 + 4 * k + 4]))[0]
             for k in range(10)]
    assert table == [0x182E4, 0, 0, 0x18458, 0x18398, 0x183E8,
                     0x18398, 0x183E8, 0x18470, 0]


def test_event_slot_block(prog):
    """The 0x28-byte callback block at 0x59400 is zero in the image (the image
    is the loader's view: BSS) and its slots are the ones the engine installs."""
    funcs, datas, _ = symbols.load()
    assert datas[EVENT_HANDLERS]["name"] == "event_handlers"
    assert datas[DIALOG_LEFT_PRESS]["addr"] == DIALOG_LEFT_PRESS
    assert datas[DIALOG_RIGHT_PRESS]["addr"] == DIALOG_RIGHT_PRESS
    assert datas[DIALOG_IDLE]["addr"] == DIALOG_IDLE
    assert datas[EVENT_PRE]["addr"] == EVENT_PRE
    # the four callback slots 3/5/7 are the graphics/status area's named ones
    for a, n in ((0x5940C, "status_mouse_callback"),
                 (0x59414, "status_frame_callback"),
                 (0x5941C, "status_click_callback")):
        assert datas[a]["name"] == n, (hex(a), datas[a]["name"])


def test_cursor_layer_and_layers_are_shared(prog):
    """The layer table and the cursor hotspot are shared with graphics/playflic;
    this object must use the same names the other TOMLs settled on."""
    funcs, datas, _ = symbols.load()
    assert datas[LAYERS]["name"] == "layers"
    assert datas[CURSOR_LAYER_ID]["name"] == "cursor_layer_id"
    assert datas[CURSOR_HOTSPOT_X]["name"] == "cursor_hotspot_x"
    assert datas[CURSOR_HOTSPOT_Y]["name"] == "cursor_hotspot_y"


def test_bss_globals_are_zero(prog):
    """The dialog engine's state lives in BSS: the image must show zeros (so
    tests can rely on a fresh Emu starting clean)."""
    img = prog.image[2]
    for a in (DIALOG_ART_BM, DIALOG_ART_DATA, EDIT_BUFFER, EDIT_CURSOR,
              AUTO_REPEAT, MOUSE_IN_PREVIEW, DIALOG_RESULT, DIALOG_SOUNDS,
              LAST_KEY, DIALOG_RUNNING, LEFT_HELD, UI_MOUSE_X, UI_MOUSE_Y,
              UI_NET_FORWARD, UI_BUTTON_BITS, OUTRO_DONE, OUTRO_IS_ORC,
              OUTRO_FRAME, OUTRO_TICK):
        assert a >= 0x5853C, hex(a)
        assert bytes(img[a - 0x50000:a - 0x50000 + 2]) == b"\0\0", hex(a)


def test_alt_font_slot(prog):
    """0x59220 (alt_font) is a Font record filled at run time: it is in BSS
    (the image shows zeros) and is not the default font 0x55444.  Four screens
    store its address in cur_font (0x152bb, 0x18fee, 0x19ef7, 0x1c42d)."""
    funcs, datas, _ = symbols.load()
    img = prog.image[2]
    assert datas[ALT_FONT]["name"] == "alt_font"
    assert ALT_FONT >= 0x5853C and ALT_FONT != 0x55444
    assert bytes(img[ALT_FONT - 0x50000:ALT_FONT - 0x50000 + 4]) == b"\0\0\0\0"


from wc1.emu import Emu  # noqa: E402  (imported late: only the T4 tests need it)
