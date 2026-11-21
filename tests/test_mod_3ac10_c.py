import os
import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')

SRC = path('src/mod_3ac10', 'hline_reference.c')

BM = {}


def init_emu(emu):
    BM['bm'] = emu.alloc(16, 16)
    BM['pix'] = emu.alloc(0x4000, 16)


def _setup(width, color):
    def f(emu):
        import struct
        emu.write(BM['pix'], bytes(0x4000))
        emu.write(BM['bm'], struct.pack('<hhI', width, 64, BM['pix']))
    return f


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_3ac10'), [])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_3ac10'), ['hline_reference.c'])


def test_h_line():
    from wc1 import symbols  # noqa: F401
    by = t4spec.by_link_lenient()
    cb = by['_cur_bitmap']['addr'] if '_cur_bitmap' in by else None
    dc = by['_draw_color']['addr'] if '_draw_color' in by else None
    assert cb is not None and dc is not None
    import struct

    def mk(x, y, ln, width, color):
        def setup(emu):
            emu.write(BM['pix'], bytes(0x4000))
            emu.write(BM['bm'], struct.pack('<hhI', width, 64, BM['pix']))
            emu.write(cb, struct.pack('<I', BM['bm']))
            emu.write(dc, bytes([color]))
        return T4Case(args=(x, y, ln), setup=setup, label=f"{x},{y},{ln}")

    cases = [
        mk(0, 0, 0, 320, 7),
        mk(0, 0, 1, 320, 7),
        mk(5, 3, 20, 320, 0x55),
        mk(10, 2, 100, 64, 0xFF),
        mk(-3, 4, 8, 64, 9),
        mk(0, 10, 200, 128, 1),
    ]
    watch = []

    def init(emu):
        init_emu(emu)
        watch[:] = [(BM['pix'], 0x4000)]

    t4spec.run_spec(SRC, 'HLine_', 0x3ac10, cases,
                    out_regs=(), init_emu=init,
                    watch=watch,
                    extra=None)
