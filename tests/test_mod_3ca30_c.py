import os
import random
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_3ca30', 'draw_glyph_2bpp_reference.c')

DEST = 0x5ACF6
BUFS = {}


def init_emu(emu):
    BUFS['dst'] = emu.alloc(0x2000, 16)
    BUFS['tbl'] = emu.alloc(0x400, 16)


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_3ca30'), [])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_3ca30'), ['draw_glyph_2bpp_reference.c'])


def _mk(rng):
    ch = rng.randrange(0x20, 0x24)
    rows = rng.randrange(1, 4)
    bpr = rng.randrange(1, 3)
    maxx = rng.randrange(0, 16)
    first = 0x20
    tbl = bytearray(rng.randrange(256) for _ in range(0x400))
    for i in range(4):
        off = 0x40 + i * 8
        tbl[(i * 3):(i * 3) + 2] = struct.pack('<H', off)
        tbl[i * 3 + 2] = rng.randrange(0, 9)
    colors = bytes([0, rng.randrange(256), rng.randrange(256), rng.randrange(256)])

    def setup(emu):
        d, t = BUFS['dst'], BUFS['tbl']
        emu.write(d, bytes(rng.randrange(256) for _ in range(0x2000)) if False else b'\x55' * 0x2000)
        emu.write(t, bytes(tbl))
        emu.write(DEST, struct.pack('<I', d + 0x100))
    return tbl, colors, rows, bpr, maxx, first, ch, setup


def _case(rng):
    tbl, colors, rows, bpr, maxx, first, ch, setup = _mk(rng)

    def setup2(emu):
        setup(emu)
    c = T4Case(args=(ch,), setup=setup2)
    c.mem = {}
    return c, (tbl, colors, rows, bpr, maxx, first)


def test_draw_glyph_2bpp():
    # Globals are located via the symbol DB through extra=; use setup to fill them.
    from wc1 import symbols
    from wc1.t4spec import by_link_lenient
    bl = by_link_lenient()
    a = lambda n: bl['_' + n]['addr']
    rng = random.Random(0x3CA30)
    cases = []
    for i in range(12):
        tbl, colors, rows, bpr, maxx, first, ch, _ = _mk(rng)

        def setup(emu, tbl=tbl, colors=colors, rows=rows, bpr=bpr, maxx=maxx, first=first):
            d, t = BUFS['dst'], BUFS['tbl']
            emu.write(d, b'\x55' * 0x2000)
            emu.write(t, bytes(tbl))
            emu.write(a('text_dest'), struct.pack('<I', d + 0x100))
            emu.write(a('text_glyph_table'), struct.pack('<I', t))
            emu.write(a('text_max_x'), struct.pack('<H', maxx))
            emu.write(a('text_bytes_per_row'), bytes([bpr]))
            emu.write(a('text_rows'), bytes([rows]))
            emu.write(a('text_colors'), colors)
            emu.write(a('text_first_char'), bytes([first]))
        cases.append(T4Case(args=(ch,), setup=setup, label='c%d' % i))
    t4spec.run_spec(
        SRC, 'DrawGlyph2bpp_', 0x3ca30, cases,
        out_regs=('eax',),
        init_emu=init_emu,
        watch=[(a('text_dest'), 4)],
    )
