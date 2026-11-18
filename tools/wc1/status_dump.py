"""Dump the STATUS.C panel data: the per-unit-type command cards, the button
geometry, the string pool and the panel rects (all read from the loaded image,
so LE relocations are applied).

usage: python3 -m wc1.status_dump [card-id ...]

A "card" is one entry of unit_panel_table (0x549c4): its id is a unit type
0x00..0x34 or one of the build menus 0x35..0x3c.  With no arguments every card
that has buttons is printed.
"""
import struct
import sys

from . import analysis

TABLE = 0x549C4
BUTTON_RECT = 0x514E4
NAMES = 0x54E54
INFO_RECT = 0x53590
PANEL_RECT = 0x53570


def _card_slots():
    p = analysis.run()
    img = p.image[p.data.index]
    base = p.data.base
    w = lambda a: struct.unpack_from("<H", img, a - base)[0]
    dw = lambda a: struct.unpack_from("<I", img, a - base)[0]
    return p, img, base, w, dw


def _text(p, a):
    img = p.image[p.data.index]
    base = p.data.base
    s = b""
    while img[a - base] != 0:
        s += bytes([img[a - base]])
        a += 1
    return s.decode("latin-1")


def plain(text):
    """Drop the @1/@2 colour escapes of the button labels."""
    out = ""
    i = 0
    while i < len(text):
        if text[i] == "@" and i + 1 < len(text) and text[i + 1].isdigit():
            i += 2
            continue
        out += text[i]
        i += 1
    return out


def main():
    p, img, base, w, dw = _card_slots()
    ids = [int(a, 0) for a in sys.argv[1:]] or range(0x3D)
    print("panel rect    ", struct.unpack_from("<6h", img, PANEL_RECT - base))
    print("info rect     ", struct.unpack_from("<6h", img, INFO_RECT - base))
    print("button slots  ")
    for i in range(6):
        print("   slot %d" % i, struct.unpack_from("<6h", img, BUTTON_RECT - base + 12 * i))
    print("string pool: 0x57d50..0x57dd9")
    for a in (0x57D40, 0x57D50, 0x57D5C, 0x57D64, 0x57D70, 0x57D7C, 0x57D80, 0x57D90,
              0x57DA0, 0x57DC8, 0x57DD8, 0x57DE8):
        print("   %#07x %r" % (a, _text(p, a)))
    for t in ids:
        a = TABLE + 14 * t
        n = w(a)
        buttons = dw(a + 2)
        name = dw(NAMES + 8 * t + 4)
        title = _text(p, name) if name else "menu"
        print("\ncard %#04x (%s): %d button(s), changed=%#x draw=%#x"
              % (t, title, n, dw(a + 6), dw(a + 10)))
        for i in range(n if buttons else 0):
            e = buttons + 0x14 * i
            print("   %#07x slot=%d face=%#04x avail=%#07x key=%#04x kind=%d arg=%#04x "
                  "action=%#07x  %r"
                  % (e, w(e), w(e + 2), dw(e + 4), img[e - base + 12], img[e - base + 13],
                     img[e - base + 14], dw(e + 15), plain(_text(p, dw(e + 8)))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
