"""T4 differential tests of the video library: the compiled reference C of
src/graphics/ against the original functions under wc1.emu (docs/GOAL.md M1).

Every test runs both implementations on identical inputs and compares the
result registers and the touched memory (and, for the DAC/port writers, the
sequence of port writes).  The T3-matched functions of this area are checked
by wc1.match instead (see analysis/symbols/graphics.toml).
"""
import os
import struct

import pytest

from wc1 import cemu, path

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM (nix develop)")

CUR_BITMAP = 0x55438
DRAW_COLOR = 0x5AD30
BACKBUF_BM = 0x5A870
LAYERS = 0x5AA90
CURSOR_IMAGE = 0x5AA60
CURSOR_LAYER_ID = 0x5AA78
CURSOR_SAVE_BM = 0x5AD10
CURSOR_SAVE_RECT = 0x5AD18
MOUSE_RAW_X, MOUSE_RAW_Y = 0x5A8B0, 0x5A8B2
MOUSE_X, MOUSE_Y = 0x5A8CA, 0x5A8CC
DIRTY = 0x5ACD0
CUR_FONT = 0x5ACF0
TEXT_GLYPH_FN = 0x5AD07
TEXT_ESC = 0x5AD0B
PALETTE_BASE, PALETTE_CUR = 0x5AD60, 0x5B060
PALETTE_CYCLES = 0x628A0
KEY_MODIFIERS = 0x5AD50

VLINE = 0x32970
FILL_RECT = 0x326A0
BITMAP_CLEAR = 0x31FC0
BITMAP_BLIT = 0x32410
BITMAP_BLIT_T = 0x325D0
BITMAP_BLIT_T_ALL = 0x326F0
TEXT_WIDTH = 0x32060
DRAWTEXT = 0x31DCC
TEXT_SET_COLOR = 0x32030
CURSOR_SET_IMAGE = 0x317B0
CURSOR_MOVE_TO = 0x330A0
CURSOR_RESTORE = 0x32188
SCREEN_UPDATE = 0x321E8
LAYER_FILL_CALLBACK = 0x32F10
PALETTE_SET = 0x33150
VGA_SET_RANGE = 0x331BE
CYCLE_STEP_LIST = 0x33220
CYCLES_UPDATE = 0x33324
EVT_PROCESS = 0x32B40
DIRTY_ALIGN_PRESENT = 0x33AA0

LAYER_FILL = 0x32F10
BITMAP_BLIT_TRANSPARENT = 0x325D0


def stub_memmove(emu):
    """Flat model of the clib memmove (0x3cefc): its body moves DS into ES and
    runs a rep movsd, which Unicorn cannot execute (same reason as the
    built-in memcpy model in wc1.emu).  Both the original and the compiled C
    call 0x3cefc, so one stub serves the pair."""
    def memmove(e):
        dst, src, n = e.reg("eax"), e.reg("edx"), e.reg("ebx")
        if n:
            e.write(dst, e.read(src, n))
        return dst
    emu.stubs[0x3CEFC] = memmove


def load(module):
    """A fresh emulator and the compiled reference module of src/graphics/."""
    from wc1.emu import Emu
    emu = Emu()
    cm = cemu.load(emu, path("src", "graphics", module))
    return emu, cm


def screen(emu, w=64, h=32, fill=0):
    """Install a scratch bitmap as cur_bitmap; returns (bitmap, data)."""
    data = emu.alloc(w * h)
    emu.write(data, bytes([fill]) * (w * h))
    bm = emu.alloc(8)
    emu.write(bm, struct.pack("<HHI", w, h, data))
    emu.put_u32(CUR_BITMAP, bm)
    return bm, data, w, h


def bitmap(emu, w, h, rows):
    data = emu.alloc(w * h)
    emu.write(data, bytes(rows))
    bm = emu.alloc(8)
    emu.write(bm, struct.pack("<HHI", w, h, data))
    return bm


def rect(emu, x1, y1, x2, y2, w=None, h=None):
    r = emu.alloc(12)
    if w is None:
        w = x2 - x1 + 1
    if h is None:
        h = y2 - y1 + 1
    emu.write(r, struct.pack("<6h", x1, y1, x2, y2, w, h))
    return r


def layer(emu, index, active, x, y, w, h, data, callback):
    emu.write(LAYERS + index * 18, struct.pack("<HhhhhII", active, x, y, w, h, data, callback))


def run_pair_io(emu, addr, cm, name, *args, watch, out_regs=(), cdecl=False):
    """run_pair + comparison of the port-write sequence (DAC access)."""
    saved = [(a, emu.read(a, n)) for a, n in watch]
    log = []
    emu.on_io = lambda e, port, size, value: log.append((port, size, value))
    emu.call(addr, *args, cdecl=cdecl)
    log_orig = list(log)
    mem_orig = [(a, emu.read(a, n)) for a, n in watch]
    for a, d in saved:
        emu.write(a, d)
    del log[:]
    cm.call(name, *args, cdecl=cdecl)
    log_c = list(log)
    mem_c = [(a, emu.read(a, n)) for a, n in watch]
    diffs = []
    if log_orig != log_c:
        diffs.append(f"port writes: original {log_orig[:8]}... != C {log_c[:8]}...")
    for (a, _), x, y in zip(watch, mem_orig, mem_c):
        if x != y:
            for k in range(len(x)):
                if x[k] != y[k]:
                    diffs.append(f"memory {a + k:#x}: original {x[k]:02x} != C {y[k]:02x}")
                    break
    return diffs


# --------------------------------------------------------------- primitives

def test_t4_vline():
    emu, cm = load("gfx_prim.c")
    bm, data, w, h = screen(emu, 64, 32)
    emu.write(DRAW_COLOR, b"\x07")
    for args in ((5, 3, 10), (0, 0, 1), (60, 1, 8)):
        diffs = cemu.run_pair(emu, VLINE, cm, "VLine_", *args, watch=[(data, w * h)], out_regs=())
        assert diffs == [], (args, diffs)


def test_t4_fill_rect():
    emu, cm = load("blit.c")
    bm, data, w, h = screen(emu, 64, 32)
    emu.write(DRAW_COLOR, b"\x05")
    for args in ((2, 3, 10, 4), (0, 0, 1, 1), (50, 20, 12, 10)):
        diffs = cemu.run_pair(emu, FILL_RECT, cm, "FillRect_", *args, watch=[(data, w * h)], out_regs=())
        assert diffs == [], (args, diffs)


def test_t4_bitmap_clear():
    emu, cm = load("blit.c")
    bm, data, w, h = screen(emu, 64, 32, 0xFF)
    diffs = cemu.run_pair(emu, BITMAP_CLEAR, cm, "BitmapClear_", 0x33, watch=[(data, w * h)], out_regs=())
    assert diffs == [], diffs


def _blit_case(emu, cm, name, orig, transparent=False):
    dst_bm, dst, dw, dh = screen(emu, 40, 20)
    src = bitmap(emu, 8, 6, [0, 1, 2, 3, 4, 5, 0, 7] * 6)
    r = rect(emu, 0, 0, 7, 5, 8, 6)
    for x, y in ((3, 2), (-2, 1), (36, 18)):
        diffs = cemu.run_pair(emu, orig, cm, name, x, y, src, r,
                              watch=[(dst, 40 * 20), (r, 12)], out_regs=())
        assert diffs == [], (name, x, y, diffs)


def test_t4_bitmap_blit():
    emu, cm = load("blit.c")
    _blit_case(emu, cm, "BitmapBlit_", BITMAP_BLIT)


def test_t4_bitmap_blit_transparent():
    emu, cm = load("blit.c")
    _blit_case(emu, cm, "BitmapBlitTransparent_", BITMAP_BLIT_T)


def test_t4_bitmap_blit_transparent_all():
    emu, cm = load("blit.c")
    dst_bm, dst, dw, dh = screen(emu, 40, 20)
    src = bitmap(emu, 8, 6, [0, 1, 2, 3, 4, 5, 6, 7] * 6)
    for x, y in ((3, 2), (-2, 1), (36, 18)):
        diffs = cemu.run_pair(emu, BITMAP_BLIT_T_ALL, cm,
                              "BitmapBlitTransparentAll_", x, y, src,
                              watch=[(dst, 40 * 20)], out_regs=())
        assert diffs == [], (x, y, diffs)


# --------------------------------------------------------------------- text

def _font(emu):
    from wc1.resources_war import WarArchive
    raw = WarArchive().read(0xD7 - 2)
    base = emu.alloc(len(raw) + 16)
    emu.write(base, raw[:4])
    table = base + 8
    emu.write(table, raw[4:])
    emu.put_u32(base + 4, table)
    emu.put_u32(CUR_FONT, base)
    emu.call(TEXT_SET_COLOR, 100)
    return raw, base


def test_t4_text_width():
    emu, cm = load("text.c")
    raw, font = _font(emu)
    for s in ("Gold 100", "Hello\nWorld", "a\tb", "@1Red@2Blue@@"):
        p = emu.alloc(64)
        emu.write(p, s.encode() + b"\0")
        diffs = cemu.run_pair(emu, TEXT_WIDTH, cm, "TextWidth_", font, p)
        assert diffs == [], (s, diffs)


def test_t4_draw_text():
    emu, cm = load("text.c")
    raw, font = _font(emu)
    for s, x, y in (("Gold 100", 3, 2), ("Hi\nthere", 0, 0), ("@1A@2B@@", 1, 1)):
        bm, data, w, h = screen(emu, 160, 24)
        p = emu.alloc(64)
        emu.write(p, s.encode() + b"\0")
        diffs = cemu.run_pair(emu, DRAWTEXT, cm, "DrawText_", x, y, p,
                              watch=[(data, w * h), (0x5ACF4, 0x18)], out_regs=())
        assert diffs == [], (s, diffs)


# ------------------------------------------------------------------- cursor

def test_t4_cursor_set_image():
    emu, cm = load("cursor.c")
    desc = bitmap(emu, 8, 8, [1] * 64) - 4           # hotspot words then Bitmap
    emu.write(desc, struct.pack("<hh", 2, 3))
    emu.write(MOUSE_RAW_X, struct.pack("<h", 50))
    emu.write(MOUSE_RAW_Y, struct.pack("<h", 40))
    layer(emu, 0, 1, 0, 0, 8, 8, 0, BITMAP_BLIT_TRANSPARENT)
    dirty = [(0x5AA60, 0x18), (LAYERS, 18), (MOUSE_X, 4), (DIRTY, 12)]
    diffs = cemu.run_pair(emu, CURSOR_SET_IMAGE, cm, "CursorSetImage_", desc,
                          watch=dirty, out_regs=())
    assert diffs == [], diffs


def test_t4_cursor_move_to():
    emu, cm = load("cursor.c")
    emu.write(CURSOR_IMAGE, struct.pack("<hh", 2, 3))
    emu.write(MOUSE_RAW_X, struct.pack("<h", 10))
    emu.write(MOUSE_RAW_Y, struct.pack("<h", 10))
    layer(emu, 0, 1, 0, 0, 8, 8, 0, BITMAP_BLIT_TRANSPARENT)
    emu.write(DIRTY, struct.pack("<6h", 0x7FFF, 0x7FFF, -0x8000, -0x8000, 0, 0))
    for x, y in ((20, 30), (0, 0), (319, 199)):
        diffs = cemu.run_pair(emu, CURSOR_MOVE_TO, cm, "CursorMoveTo_", x, y,
                              watch=[(LAYERS, 18), (MOUSE_X, 4), (DIRTY, 12)],
                              out_regs=())
        assert diffs == [], (x, y, diffs)


def test_t4_cursor_restore_under():
    emu, cm = load("cursor.c")
    dst = bitmap(emu, 40, 20, [0] * 800)
    emu.write(BACKBUF_BM, emu.read(dst, 8))
    save = bitmap(emu, 16, 16, [0x42] * 256)
    emu.write(CURSOR_SAVE_BM, emu.read(save, 8))
    emu.write(CURSOR_SAVE_RECT, struct.pack("<6h", 0, 0, 15, 15, 16, 16))
    layer(emu, 0, 1, 5, 4, 16, 16, 0, BITMAP_BLIT_TRANSPARENT)
    diffs = cemu.run_pair(emu, CURSOR_RESTORE, cm, "CursorRestoreUnder_",
                          watch=[(0x5A874, 4), (CURSOR_SAVE_RECT, 12),
                                 (0x5AD14, 4)], out_regs=())
    bm_data = emu.u32(0x5A874)
    assert diffs == [], diffs
    assert emu.read(bm_data + 4 * 40 + 5, 3) == b"\x42\x42\x42"


def test_t4_layer_fill_callback():
    emu, cm = load("cursor.c")
    bm, data, w, h = screen(emu, 40, 20, 0x7F)
    emu.write(DIRTY, struct.pack("<6h", 2, 3, 10, 8, 9, 6))
    r = rect(emu, 0, 0, 5, 5)
    diffs = cemu.run_pair(emu, LAYER_FILL_CALLBACK, cm, "LayerFillCallback_",
                          1, 2, r, 0, watch=[(data, w * h), (DRAW_COLOR, 1)],
                          out_regs=())
    assert diffs == [], diffs


def test_t4_screen_update():
    emu, cm = load("cursor.c")
    emu.stubs[DIRTY_ALIGN_PRESENT] = lambda e: None
    back = bitmap(emu, 320, 200, [0] * 64000)
    emu.write(BACKBUF_BM, emu.read(back, 8))
    save = bitmap(emu, 16, 16, [0] * 256)
    emu.write(CURSOR_SAVE_BM, emu.read(save, 8))
    cursor = bitmap(emu, 8, 8, [3] * 64)
    emu.write(CURSOR_IMAGE, struct.pack("<hh", 0, 0))
    emu.write(LAYERS, b"\0" * (32 * 18))
    layer(emu, 2, 1, 0, 0, 320, 200, 0, LAYER_FILL)
    layer(emu, 0, 1, 4, 4, 8, 8, cursor, BITMAP_BLIT_TRANSPARENT)
    emu.write(DIRTY, struct.pack("<6h", 2, 3, 30, 25, 29, 23))
    watch = [(BACKBUF_BM, 8), (LAYERS, 32 * 18), (DIRTY, 12),
             (CURSOR_SAVE_BM, 0x14), (CUR_BITMAP, 4), (DRAW_COLOR, 1)]
    back_data = emu.u32(BACKBUF_BM + 4)
    save_data = emu.u32(CURSOR_SAVE_BM + 4)
    watch += [(back_data, 320 * 40), (save_data, 256)]
    diffs = cemu.run_pair(emu, SCREEN_UPDATE, cm, "ScreenUpdate_", watch=watch, out_regs=())
    assert diffs == [], diffs


# ------------------------------------------------------------------ palette

def test_t4_vga_set_palette_range():
    emu, cm = load("palette.c")
    rgb = emu.alloc(64)
    emu.write(rgb, bytes(range(64)))
    diffs = run_pair_io(emu, VGA_SET_RANGE, cm, "_VgaSetPaletteRange",
                        rgb, 1, 5, watch=[(rgb, 64)], cdecl=True)
    assert diffs == [], diffs


def test_t4_palette_set():
    emu, cm = load("palette.c")
    rgb = emu.alloc(768)
    emu.write(rgb, bytes([(i * 7) & 0xFF for i in range(768)]))
    diffs = run_pair_io(emu, PALETTE_SET, cm, "PaletteSet_", 4, 16, rgb,
                        watch=[(PALETTE_BASE, 768), (PALETTE_CUR, 768)])
    assert diffs == [], diffs


def test_t4_palette_cycle_step_list():
    emu, cm = load("palette.c")
    emu.on_io = lambda e, port, size, value: None
    cols = emu.alloc(12)
    emu.write(cols, bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))
    emu.write(PALETTE_CYCLES, struct.pack("<HBBBBBIB", 1, 4, 4, 3, 0, 5, cols, 4))
    emu.write(PALETTE_CUR, bytes(768))
    diffs = cemu.run_pair(emu, CYCLE_STEP_LIST, cm, "PaletteCycleStepList_", 0,
                          watch=[(PALETTE_CYCLES, 12), (PALETTE_CUR, 768)],
                          out_regs=())
    assert diffs == [], diffs


def test_t4_palette_cycles_update():
    emu, cm = load("palette.c")
    emu.on_io = lambda e, port, size, value: None
    stub_memmove(emu)
    for explicit in (False, True):
        emu.write(PALETTE_CYCLES, bytes(0xC0))
        emu.write(PALETTE_CUR, bytes([(i * 3) & 0xFF for i in range(768)]))
        if explicit:
            cols = emu.alloc(12)
            emu.write(cols, bytes([11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43]))
            emu.write(PALETTE_CYCLES, struct.pack("<HBBBBBIB", 1, 2, 2, 5, 0, 9, cols, 4))
            emu.write(PALETTE_CYCLES + 12, struct.pack("<HBBBBBIB", 1, 1, 1, 3, 0, 4, 0, 0))
        else:
            emu.write(PALETTE_CYCLES, struct.pack("<HBBBBBIB", 1, 2, 2, 5, 0, 9, 0, 0))
            emu.write(PALETTE_CYCLES + 12, struct.pack("<HBBBBBIB", 0, 1, 1, 3, 0, 4, 0, 0))
        diffs = cemu.run_pair(emu, CYCLES_UPDATE, cm, "PaletteCyclesUpdate_",
                              watch=[(PALETTE_CYCLES, 0xC0), (PALETTE_CUR, 768)],
                              out_regs=())
        assert diffs == [], (explicit, diffs)


# ------------------------------------------------------------------- events

def test_t4_evt_process():
    emu, cm = load("evt_process.c")
    ev = emu.alloc(12)
    cases = [(0x80, 0x2a), (0x100, 0x2a), (0x80, 0x3a), (0x100, 0x36),
             (0x80, 0x47), (0x100, 0x1d), (0x400, 0), (0, 0x1d),
             (0x80, 0x1e), (0x80, 0x39)]
    for typ, scan in cases:
        for mods in (0x00, 0x01, 0x02, 0x04, 0x20, 0x40):
            emu.write(KEY_MODIFIERS, struct.pack("<B", mods))
            emu.write(0x5A8D4, bytes(0x100))
            emu.write(ev, struct.pack("<HHhhBBH", typ, 0, 0, 0, scan, 0, 0))
            diffs = cemu.run_pair(emu, EVT_PROCESS, cm, "EvtProcess_", ev,
                                  watch=[(ev, 12), (KEY_MODIFIERS, 1),
                                         (0x5A8D4, 0x100)], out_regs=())
            assert diffs == [], (hex(typ), hex(scan), hex(mods), diffs)
