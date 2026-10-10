"""Differential tests (T4) of the graphics library against small Python models,
using the original code under the Unicorn harness. Text uses the real font
resource 0xd7 from DATA.WAR."""
import os
import struct

import pytest

from wc1 import path

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe"))
         and os.path.exists(path("original", "cd", "files", "DATA", "DATA.WAR"))),
    reason="original files not extracted")

CUR_BITMAP, DRAW_COLOR = 0x55438, 0x5AD30
HLINE, VLINE, CLEAR, TEXT, SETCOL, TEXTW = 0x3AC10, 0x32970, 0x31FC0, 0x31DCC, 0x32030, 0x32060
GRPFRAME = 0x33110


def make_screen(emu, w=64, h=32, fill=0):
    data = emu.alloc(w * h)
    emu.write(data, bytes([fill]) * (w * h))
    bm = emu.alloc(8)
    emu.write(bm, struct.pack("<HHI", w, h, data))
    emu.put_u32(CUR_BITMAP, bm)
    return bm, data, w, h


def test_hline_vline_clear():
    from wc1.emu import Emu
    emu = Emu()
    bm, data, w, h = make_screen(emu)
    emu.write(DRAW_COLOR, bytes([7]))
    emu.call(HLINE, 5, 3, 10)
    emu.call(VLINE, 20, 4, 6)
    want = bytearray(w * h)
    for i in range(10):
        want[3 * w + 5 + i] = 7
    for i in range(6):
        want[(4 + i) * w + 20] = 7
    assert emu.read(data, w * h) == bytes(want)
    emu.call(CLEAR, 9)
    assert emu.read(data, w * h) == bytes([9]) * (w * h)


def test_grp_frame_bitmap():
    from wc1.emu import Emu
    emu = Emu()
    grp = emu.alloc(64)
    # header: count(2) maxw maxh, frame 0: xoff yoff w h offset ; frame 1 ...
    blob = struct.pack("<HBB", 2, 9, 8) + struct.pack("<BBBBI", 1, 2, 5, 4, 28) + \
        struct.pack("<BBBBI", 0, 0, 3, 2, 48)
    emu.write(grp, blob.ljust(64, b"\0"))
    out = emu.alloc(8)
    emu.call(GRPFRAME, grp, 1, out)
    w, h, data = struct.unpack("<HHI", emu.read(out, 8))
    assert (w, h, data) == (3, 2, grp + 48)


def _font(emu):
    from wc1.resources_war import WarArchive
    raw = WarArchive().read(0xD7 - 2)
    base = emu.alloc(len(raw) + 16)
    emu.write(base, raw[:4])
    # the resource loader keeps the 4 header bytes and stores at +4 a pointer
    # to the rest of the resource (the glyph table = file bytes 4..)
    table = base + 8
    emu.write(table, raw[4:])
    emu.put_u32(base + 4, table)
    return raw, base


def model_text(raw, s, x0=0):
    first, bpr, rows = raw[0], raw[1], raw[2]
    table = raw[4:]
    out = {}
    x = x0
    for ch in s.encode():
        off, w = struct.unpack_from("<HB", table, (ch - first) * 3)
        for r in range(rows):
            for px in range(w):
                byte = table[off + r * ((w + 3) // 4) + px // 4]
                v = (byte >> (2 * (px % 4))) & 3
                if v:
                    out[(x + px, r)] = v
        x += w
    return out, x


def test_draw_text_matches_model():
    from wc1.emu import Emu
    emu = Emu()
    raw, font = _font(emu)
    bm, data, w, h = make_screen(emu, 160, 24)
    emu.put_u32(0x5ACF0, font)
    emu.call(SETCOL, 100)               # pixel values 1..3 -> colours 100..102
    s = "Gold 100"
    str_p = emu.alloc(32)
    emu.write(str_p, s.encode() + b"\0")
    emu.call(TEXT, 3, 2, str_p)
    got = emu.read(data, w * h)
    model, end = model_text(raw, s, 3)
    want = bytearray(w * h)
    for (x, y), v in model.items():
        want[(2 + y) * w + x] = 99 + v
    assert got == bytes(want)
    assert emu.call(TEXTW, font, str_p) == end - 3
