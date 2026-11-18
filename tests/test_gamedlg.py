"""Game logic: GAMEDLG.C (0x1a3c0..0x1af20), the game's modal dialog boxes.

1. T3: every matched C file of the area still reproduces the original bytes,
   relocation targets and module-local data under Watcom 10.0a (`wc1.match`).
2. T4: the reference C of the functions that do not match byte for byte runs
   against the original under `wc1.cemu` on identical inputs - the callees
   with side effects are stubbed and their arguments recorded, as in
   tests/test_status.py and tests/test_cmd_123f0.py.
3. Structural checks: the module range and its 21 discovered starts, the
   dialog page table read out of DATA.WAR, and the module's own string pool.

Layout and per-function notes: docs/subsystems/gamedlg.md.
"""
import os
import struct

import pytest

from wc1 import analysis, cemu, match, path, resources_war, symbols
from wc1.emu import Emu

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "gamedlg")
MODULE = (0x1A3C0, 0x1AF20)

# --------------------------------------------------------------- addresses
PALETTE = 0x58F20
PALETTE_TARGET = 0x62570
BACKBUF_BM = 0x5A870               # {w, h, void *data}
CUR_BITMAP = 0x55438
LAYERS = 0x5AA90                   # 18-byte records
DIALOG_BITMAP = 0x59620
DIALOG_BUFFER = 0x59624
DIALOG_LAYER_STATE = 0x59628
DIALOG_DEPTH = 0x5963C
DIALOG_ENABLED = 0x517CC
DIALOG_ACTIVE = 0x51E24
DIRTY = 0x5ACD0
GAME_SPEED_CACHE = 0x594F0
GAME_MODE = 0x59616
SCREEN_MODE = 0x593F6
NET_PLAY = 0x52586
NET_EVENT = 0x5A11A
SCENARIO_RACE = 0x50088
PREFS = 0x532B4
SLOT_FILE = 0x59610
LOAD_NOT_CANCELLED = 0x516B0
SETUP_QUIT = 0x5176A

# callees (all named in the database)
MODAL_SCREEN = 0x1A560
DIALOG_RUN = 0x180A8
NET_PUMP = 0x19B80
GAME_INPUT_INIT = 0x1A328
DIM_SCREEN = 0x1A4B8
GDS_ALLOC = 0x32558
GDS_FREE = 0x32780
BITMAP_BLIT_ALL = 0x33B00
PALETTE_SET = 0x33150
DIRTY_ADD_BOX = 0x33A30
DIRTY_PRESENT = 0x33AA0
SCREEN_UPDATE = 0x321E8
SND_APPLY = 0x2674C
CLOCK = 0x30E98
SAVE_SLOT_CREATE = 0x14AD8
SAVE_SLOT_OPEN = 0x1498C
SAVE_WRITE_IMAGE = 0x24BF0
FCLOSE = 0x33887
NET_LINK_EXIT = 0x240F8
GAME_SAVE_DIALOG = 0x1ABC0
GAME_LOAD_DIALOG = 0x1ACCC
OPTIONS_DIALOG = 0x1A800
QUIT_DIALOG = 0x1AB50
SHOW_MESSAGE_RACE = 0x1A720


# ------------------------------------------------------------------ helpers
def _u16(emu, addr, v):
    emu.write(addr, struct.pack("<H", v & 0xFFFF))


def _u32(emu, addr, v):
    emu.write(addr, struct.pack("<I", v & 0xFFFFFFFF))


def _s32(emu, addr):
    return struct.unpack("<i", emu.read(addr, 4))[0]


def stub(emu, addr, nargs=4, size=0x20, ret=0):
    """Replace a callee with a recorder: its register arguments land in a
    scratch block the difftest watches (watcall order eax, edx, ebx, ecx)."""
    rec = emu.alloc(size)
    emu.write(rec, b"\x00" * size)

    def fn(e):
        for k in range(nargs):
            e.put_u32(rec + 4 * k, e.reg(("eax", "edx", "ebx", "ecx")[k]))
        return ret(e) if callable(ret) else ret

    emu.stubs[addr] = fn
    return rec


def stub_with_arg_out(emu, addr, ret_value, out_arg=2):
    """Like stub(), but also writes ret_value through the `out_arg`-th
    (0-based) register argument, which is a short* in these dialogs."""
    rec = emu.alloc(0x20)
    emu.write(rec, b"\x00" * 0x20)

    def fn(e):
        for k in range(4):
            e.put_u32(rec + 4 * k, e.reg(("eax", "edx", "ebx", "ecx")[k]))
        ptr = e.reg(("eax", "edx", "ebx", "ecx")[out_arg])
        e.write(ptr, struct.pack("<h", ret_value))
        return 0

    emu.stubs[addr] = fn
    return rec


def stub_text(emu, addr):
    """Record a message function's (text, id): the text pointer differs between
    the original and the compiled CONST, so record the string itself."""
    rec = emu.alloc(0x40)
    emu.write(rec, b"\x00" * 0x40)

    def fn(e):
        src = e.reg("eax")
        e.put_u32(rec + 0, e.reg("edx"))
        text = b""
        for k in range(0x40):
            ch = e.read(src + k, 1)
            if ch == b"\x00":
                break
            text += ch
        e.write(rec + 4, text)
        return 0

    emu.stubs[addr] = fn
    return rec


def load(emu, name):
    return cemu.load(emu, os.path.join(AREA, name))


def clean_reset(emu):
    """The dialog/UI globals the area's functions read, in a known state."""
    emu.write(DIALOG_DEPTH, b"\x00\x00")
    emu.write(DIALOG_ACTIVE, b"\x00\x00")
    emu.write(SCREEN_MODE, b"\x00\x00")
    emu.write(NET_PLAY, b"\x00\x00")
    emu.write(NET_EVENT, b"\x00\x00")
    emu.write(GAME_MODE, b"\x00\x00")
    emu.write(SETUP_QUIT, b"\x00\x00")
    emu.write(LOAD_NOT_CANCELLED, b"\x00\x00")
    emu.write(SLOT_FILE, b"\x00" * 4)
    emu.write(DIRTY, b"\x00" * 12)
    emu.write(DIALOG_ENABLED, struct.pack("<H", 1))


# ------------------------------------------------------- T3: matched files
def _matched_files():
    return sorted(f for f in os.listdir(AREA)
                  if f.endswith(".c") and not f.endswith("_reference.c"))


@pytest.mark.parametrize("name", _matched_files())
def test_matched_c(name):
    """Every T3 file of the area still matches the original (verified_by)."""
    src = os.path.join(AREA, name)
    out = path("build", "gamedlg", "t3_" + name + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, match.file_cflags(src), out)
    funcs, datas, _ = symbols.load(strict=False)
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.run()
    res = match.match_module(p, mod, by_link)
    bad = [(n, s, pr) for n, s, pr in res if s != "MATCH"]
    assert not bad, (src, bad)


def test_every_area_function_has_an_entry():
    """All 21 discovered starts of the range are in the database and named."""
    p = analysis.run()
    starts = {f["start"] for f in p.functions if MODULE[0] <= f["start"] < MODULE[1]}
    funcs, _, _ = symbols.load(strict=False)
    assert len(starts) == 21
    for a in starts:
        assert a in funcs, hex(a)
        assert not funcs[a]["name"].startswith("fn_"), hex(a)


# ------------------------------------------------------- T4: difftests
def test_t4_dim_screen_image():
    """0x1a4b8 DimScreenImage: the whole 320x200 back buffer is remapped to the
    dark red ramp, the full screen is marked dirty and the palette's second
    half is restored."""
    emu = Emu()
    cm = load(emu, "dim_screen_image_reference.c")
    buf = emu.alloc(0xFA00)
    # a deterministic pseudo-random image and palette
    img = bytes(((i * 37 + (i >> 8) * 11) & 0xFF) for i in range(0xFA00))
    emu.write(buf, img)
    _u16(emu, BACKBUF_BM + 0, 0x140)
    _u16(emu, BACKBUF_BM + 2, 0xC8)
    _u32(emu, BACKBUF_BM + 4, buf)
    pal = bytes(((i * 7 + 3) & 0xFF) for i in range(0x300))
    emu.write(PALETTE, pal)
    stub(emu, DIRTY_PRESENT, nargs=0)
    stub(emu, PALETTE_SET, nargs=3)
    diffs = cemu.run_pair(emu, 0x1A4B8, cm, "DimScreenImage_",
                          watch=[(buf, 0xFA00), (PALETTE_TARGET, 0x300), (DIRTY, 12),
                                 (PALETTE, 0x300)],
                          out_regs=())
    assert diffs == [], diffs


def test_t4_modal_screen():
    """0x1a560 ModalScreen: the nesting counter, the modal layer's geometry and
    the saved/restored active words of layers 13..22."""
    emu = Emu()
    cm = load(emu, "modal_screen_reference.c")
    buf = emu.alloc(0xFA00)
    emu.write(buf, b"\x00" * 0xFA00)
    clean_reset(emu)
    _u16(emu, BACKBUF_BM + 0, 0x140)
    _u16(emu, BACKBUF_BM + 2, 0xC8)
    _u32(emu, BACKBUF_BM + 4, buf)
    for i in range(32):                       # give the UI layers an active flag
        _u16(emu, LAYERS + i * 18, 1 if 13 <= i <= 22 else 0)
    rec = stub(emu, GDS_ALLOC, nargs=1, ret=lambda e: 0x500000)
    stub(emu, GDS_FREE, nargs=1)
    stub(emu, BITMAP_BLIT_ALL, nargs=3)
    stub(emu, PALETTE_SET, nargs=3)
    stub(emu, SCREEN_UPDATE, nargs=0)
    stub(emu, DIRTY_ADD_BOX, nargs=4)
    stub(emu, NET_PUMP, nargs=0)
    stub(emu, DIM_SCREEN, nargs=0)
    stub(emu, GAME_INPUT_INIT, nargs=0)
    watch = [(DIALOG_DEPTH, 2), (DIALOG_ACTIVE, 2), (DIALOG_BITMAP, 8),
             (DIALOG_BUFFER, 4), (DIALOG_LAYER_STATE, 0x14), (CUR_BITMAP, 4),
             (LAYERS, 32 * 18), (GAME_SPEED_CACHE, 4), (rec, 0x20)]
    for on, depth, enabled, dim in [(1, 0, 1, 1), (1, 1, 1, 1), (1, 0, 1, 0),
                                    (0, 1, 1, 1), (0, 2, 1, 1), (1, 0, 0, 1),
                                    (0, 1, 0, 1)]:
        clean_reset(emu)
        _u16(emu, DIALOG_ENABLED, enabled)
        _u16(emu, DIALOG_DEPTH, depth)
        for i in range(13, 23):
            _u16(emu, LAYERS + i * 18, 1)
        _u32(emu, DIALOG_LAYER_STATE, 0x11111111)
        _u32(emu, GAME_SPEED_CACHE, 3)
        diffs = cemu.run_pair(emu, MODAL_SCREEN, cm, "ModalScreen_", on, dim,
                              watch=watch, out_regs=())
        assert diffs == [], (on, depth, enabled, dim, diffs)


def test_t4_options_dialog():
    """0x1a800 OptionsDialog: the parameter block handed to the page (id, text
    layer, the two callbacks), and the preferences written back only on Ok."""
    emu = Emu()
    cm = load(emu, "options_dialog_reference.c")
    clean_reset(emu)
    rec = stub(emu, DIALOG_RUN, nargs=4, size=0x40)
    emu.stub_pops[DIALOG_RUN] = 4          # DialogRun ends in `ret 4`
    stub(emu, CLOCK, nargs=0, ret=1000)
    stub(emu, SND_APPLY, nargs=1)
    stub(emu, MODAL_SCREEN, nargs=2)

    def run(args, result):
        emu.stubs[DIALOG_RUN] = _dialog_run(rec, result)
        diffs = cemu.run_pair(emu, 0x1A800, cm, "OptionsDialog_",
                              watch=[(PREFS, 0x14), (rec, 0x40)], out_regs=())
        assert diffs == [], (args, result, diffs)

    for result in (0, 1):
        clean_reset(emu)
        _u16(emu, SCENARIO_RACE, 1)
        emu.write(PREFS, struct.pack("<5i", 4, 0x30, 0x40, 2, 3))
        run(None, result)
    clean_reset(emu)
    _u16(emu, SCENARIO_RACE, 0)
    emu.write(PREFS, struct.pack("<5i", 0, 0, 0, 0, 0))
    run(None, 0)


def _dialog_run(rec, result):
    """A DialogRun stub: record the five arguments (and the parameter block the
    fifth points at), then return `result`."""
    def fn(e):
        for k in range(4):
            e.put_u32(rec + 4 * k, e.reg(("eax", "edx", "ebx", "ecx")[k]))
        params = e.u32(e.reg("esp") + 4)
        e.put_u32(rec + 0x10, params)
        if params:
            e.write(rec + 0x14, e.read(params, 0x20))
        return result
    return fn


def test_t4_net_timeout_dialog():
    """0x1a9a4 NetTimeoutDialog: Retry restores the link state, Quit leaves the
    link, Save runs the save dialog first."""
    emu = Emu()
    cm = load(emu, "net_timeout_dialog_reference.c")
    stub(emu, MODAL_SCREEN, nargs=2)
    emu.stub_pops[DIALOG_RUN] = 4          # DialogRun ends in `ret 4`
    stub(emu, NET_LINK_EXIT, nargs=0)
    rec_save = stub(emu, GAME_SAVE_DIALOG, nargs=0, ret=0)
    watch = [(SCREEN_MODE, 2), (NET_PLAY, 2), (GAME_MODE, 2), (SETUP_QUIT, 2),
             (LAYERS, 18), (rec_save, 0x10)]
    cases = [(3, 0, 0), (3, 1, 0), (4, 0, 0), (3, 2, 1), (3, 4, 0), (0, 5, 0)]
    for mode, action, save_ok in cases:
        clean_reset(emu)
        _u16(emu, SCREEN_MODE, 1)
        _u16(emu, NET_PLAY, 1)
        _u16(emu, GAME_MODE, mode)
        _u16(emu, LAYERS, 1)
        stub(emu, DIALOG_RUN, nargs=4, ret=action)
        emu.stubs[GAME_SAVE_DIALOG] = (lambda v: (lambda e: v))(save_ok)
        diffs = cemu.run_pair(emu, 0x1A9A4, cm, "NetTimeoutDialog_",
                              watch=watch, out_regs=("eax",))
        assert diffs == [], (mode, action, save_ok, diffs)


def test_t4_game_load_dialog():
    """0x1accc GameLoadDialog: the slot stream, the cancel path and the linked
    game's two screen_mode passes."""
    emu = Emu()
    cm = load(emu, "game_load_dialog_reference.c")
    stub(emu, MODAL_SCREEN, nargs=2)
    stub(emu, FCLOSE, nargs=1)
    rec = emu.alloc(0x20)
    watch = [(SLOT_FILE, 4), (GAME_MODE, 2), (SCREEN_MODE, 2), (rec, 0x20)]
    for net, cancelled, handle in [(0, 0, 0x400000), (0, 1, 0x400000),
                                   (0, 0, 0), (1, 0, 0x400000), (1, 0, 0),
                                   (1, 1, 0x400000)]:
        clean_reset(emu)
        emu.write(rec, b"\x00" * 0x20)
        emu.stubs[SAVE_SLOT_OPEN] = _save_slot_open(rec, cancelled, handle)
        _u16(emu, NET_PLAY, net)
        _u16(emu, SCREEN_MODE, 1)
        diffs = cemu.run_pair(emu, 0x1ACCC, cm, "GameLoadDialog_",
                              watch=watch, out_regs=("eax",))
        assert diffs == [], (net, cancelled, handle, diffs)


def _save_slot_open(rec, cancelled, handle):
    """SaveSlotOpen(layer, dialog_id, short *cancelled) stub."""
    def fn(e):
        for k in range(3):
            e.put_u32(rec + 4 * k, e.reg(("eax", "edx", "ebx")[k]))
        ptr = e.reg("ebx")
        e.write(ptr, struct.pack("<h", cancelled))
        return handle
    return fn


def test_t4_game_menu_dialog():
    """0x1ae70 GameMenuDialog: the actions of the six buttons, the loop until
    one of them finishes, and the restart question."""
    emu = Emu()
    cm = load(emu, "game_menu_dialog_reference.c")
    stub(emu, MODAL_SCREEN, nargs=2)
    emu.stub_pops[DIALOG_RUN] = 4          # DialogRun ends in `ret 4`
    for addr in (GAME_SAVE_DIALOG, GAME_LOAD_DIALOG, QUIT_DIALOG):
        stub(emu, addr, nargs=0, ret=0)
    stub(emu, OPTIONS_DIALOG, nargs=0)
    rec_text = stub_text(emu, SHOW_MESSAGE_RACE)
    watch = [(GAME_MODE, 2), (LOAD_NOT_CANCELLED, 2), (rec_text, 0x30)]
    for action, result, answer in [(0, 1, 0), (1, 1, 0), (2, 0, 0),
                                   (3, 0, 1), (4, 1, 0), (5, 0, 0)]:
        clean_reset(emu)
        emu.write(rec_text, b"\x00" * 0x30)
        emu.stubs[DIALOG_RUN] = lambda e, a=action: a
        emu.stubs[GAME_SAVE_DIALOG] = lambda e, r=result: r
        emu.stubs[GAME_LOAD_DIALOG] = lambda e, r=result: r
        emu.stubs[QUIT_DIALOG] = lambda e, r=result: r
        emu.stubs[SHOW_MESSAGE_RACE] = _message_race(answer)
        diffs = cemu.run_pair(emu, 0x1AE70, cm, "GameMenuDialog_",
                              watch=watch, out_regs=())
        assert diffs == [], (action, result, answer, diffs)

    # the menu must stay open when a question is answered "no": Restart with
    # Cancel loops back to the box, which then reports Continue
    for action, answer in [(3, 0), (0, 0), (4, 0), (6, 0), (7, 0)]:
        clean_reset(emu)
        emu.write(rec_text, b"\x00" * 0x30)
        install = _install_seq(emu, action, 5)
        emu.stubs[GAME_SAVE_DIALOG] = lambda e: 0
        emu.stubs[QUIT_DIALOG] = lambda e: 0
        diffs = run_pair_seq(emu, 0x1AE70, cm, "GameMenuDialog_", install,
                            watch=watch, out_regs=())
        assert diffs == [], (action, answer, diffs)


def run_pair_seq(emu, addr, cmod, name, install, *args, watch=(), out_regs=("eax",)):
    """run_pair with a stub whose call sequence matters: `install()` is called
    before each side so both see the same first/second/... stub answers."""
    saved = [(a, emu.read(a, n)) for a, n in watch]
    install()
    emu.call(addr, *args)
    ro = {r: emu.reg(r) for r in out_regs}
    mo = [(a, emu.read(a, n)) for a, n in watch]
    for a, data in saved:
        emu.write(a, data)
    install()
    cmod.call(name, *args)
    rc = {r: emu.reg(r) for r in out_regs}
    mc = [(a, emu.read(a, n)) for a, n in watch]
    diffs = [f"{r}: original {ro[r]:#x} != C {rc[r]:#x}" for r in out_regs
             if ro[r] != rc[r]]
    for (a, _), (_, x), (_, y) in zip(watch, mo, mc):
        if x != y:
            for k in range(len(x)):
                if x[k] != y[k]:
                    diffs.append(f"memory {a + k:#x}: original {x[k]:02x} != C {y[k]:02x}")
                    break
    return diffs


def _install_seq(emu, first, then):
    """Install a DialogRun stub returning `first` once, then `then`."""
    def install():
        state = {"n": 0}

        def fn(e):
            state["n"] += 1
            return first if state["n"] == 1 else then
        emu.stubs[DIALOG_RUN] = fn
    return install


def _first_then(first, then):
    """A DialogRun stub returning `first` on its first call and `then` after."""
    state = {"n": 0}

    def fn(e):
        state["n"] += 1
        return first if state["n"] == 1 else then
    return fn


def _message_race(answer):
    def fn(e):
        return answer
    return fn


def test_t4_save_error_dialog():
    """0x1aca8 SaveErrorDialog: the local disk error vs the remote failure."""
    emu = Emu()
    cm = load(emu, "save_error_dialog_reference.c")
    rec = stub_text(emu, SHOW_MESSAGE_RACE)
    for pending in (0, 1):
        clean_reset(emu)
        _u16(emu, NET_EVENT, pending)
        emu.write(rec, b"\x00" * 0x40)
        diffs = cemu.run_pair(emu, 0x1ACA8, cm, "SaveErrorDialog_",
                              watch=[(rec, 0x30)], out_regs=())
        assert diffs == [], (pending, diffs)
        # the message text is compared by content, not by CONST address
    assert True


# ---------------------------------------------------------- structural
def test_dialog_page_table():
    """The page ids the module passes are the dialog pages of DATA.WAR: 0x172
    the game menu, 0x189 the quit box, 0x1d4 the victory box, 0x170/0x171 the
    network timeout box, 0x174/0x187 the load/save slot lists."""
    if not os.path.exists(resources_war.DATA_WAR):
        pytest.skip("needs original/install/DATA.WAR")
    war = resources_war.WarArchive()
    want = {
        0x170: b"Remote system is not responding!",
        0x171: b"Remote system is not responding!",
        0x172: b"@1S@2ave Game",
        0x174: b"Load Game",
        0x187: b"Save Game",
        0x189: b"Quit to DOS or Main Menu?",
        0x1D4: b"You are victorious!",
    }
    for rid, text in want.items():
        data = war.read(rid - resources_war.ID_BIAS)
        assert text in data, (hex(rid), text, data[:80])
    assert b"@1S@2ave" in war.read(0x1D4 - resources_war.ID_BIAS)
    assert b"@1S@2ave" in war.read(0x172 - resources_war.ID_BIAS)


def test_module_strings_and_range():
    """The module's own string pool (0x51e26..0x51f00, 0x56bf8..0x56c31) and the
    GAMEDLG.C range of analysis/modules.toml."""
    import tomllib
    p = analysis.run()
    img = bytes(p.image[p.data.index])
    base = p.data.base

    def cstr(a):
        i = a - base
        out = b""
        while img[i] != 0:
            out += bytes([img[i]])
            i += 1
        return out

    assert cstr(0x51E26) == b"Warcraft version numbers are different."
    assert cstr(0x51E4E) == b"Saved game uses old version number!"
    assert cstr(0x51E72) == b"Cannot play a two player game\nagainst the computer."
    assert cstr(0x51EA6) == b"Disk Error!  Unable to save game!"
    assert cstr(0x51EC8) == b"Remote system failed to save game!"
    assert cstr(0x56BF8) == b"Error saving game!"
    assert cstr(0x56C0C) == b"You failed to achieve victory..."
    assert cstr(0x56C30) == b"Are you sure you want to restart the scenario?"
    mods = tomllib.load(open(path("analysis", "modules.toml"), "rb"))["module"]
    m = next(m for m in mods if m["name"] == "GAMEDLG.C")
    assert (m["start"], m["end"]) == MODULE
