import os
import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_33b00', 'bitmap_blit_all_reference.c')
BLIT = 0x33b00 + 0  # placeholder, replaced below
BITMAP_BLIT_STUB = None

_BUF = {'bmp': 0x300000}


def _init(emu):
    try:
        emu.uc.mem_map(_BUF['bmp'], 0x10000)
    except Exception:
        pass


def _case(x, y, w, h, label):
    def setup(emu):
        import struct
        emu.write(_BUF['bmp'], struct.pack('<hh', w, h))
    c = T4Case(args=(x & 0xFFFF, y & 0xFFFF, 0), setup=setup, label=label)
    return c


def _mk(x, y, w, h, label):
    def setup(emu):
        import struct
        emu.write(_BUF['bmp'], struct.pack('<hh', w, h))
    c = T4Case(args=(x & 0xFFFF, y & 0xFFFF, _BUF['bmp']), setup=setup, label=label)
    return c


def test_t3_files():
    t4spec.assert_t3_matches(path('src/mod_33b00'), [])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_33b00'), ['bitmap_blit_all_reference.c'])


def test_bitmap_blit_all():
    from wc1 import symbols
    by = t4spec.by_link_lenient()
    blit_addr = by['BitmapBlit_']['addr']
    cases = [
        _mk(0, 0, 1, 1, 'one'),
        _mk(10, 20, 16, 16, 'basic'),
        _mk(-5, -7, 320, 200, 'neg'),
        _mk(100, 50, 0, 0, 'zero'),
        _mk(1, 2, -1, 32767, 'edge'),
    ]
    t4spec.run_spec(
        SRC, 'BitmapBlitAll_', 0x33b00, cases,
        stubs=[T4Stub(blit_addr, log_regs=('eax', 'edx', 'ebx', 'ecx'))],
        out_regs=(), init_emu=_init)
