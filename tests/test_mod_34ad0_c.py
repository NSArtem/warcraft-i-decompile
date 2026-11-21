import os

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_34ad0', 'line_reference.c')

CUR_BITMAP = 0x55438
DRAW_COLOR = 0x5ad30
HLINE_ADDR = 0x3ac10
VLINE_ADDR = 0x32970
BMP = {}
WATCH = []


def init_emu(emu):
    BMP['hdr'] = emu.alloc(16, 16)
    BMP['pix'] = emu.alloc(0x4000, 16)
    emu.put_u32(BMP['hdr'], 0x00800080)
    emu.put_u32(BMP['hdr'] + 4, BMP['pix'])
    WATCH[:] = [(BMP['pix'], 0x4000)]
    emu.put_u32(CUR_BITMAP, BMP['hdr'])
    emu.write(DRAW_COLOR, bytes([0xAB]))


def _case(x0, y0, x1, y1, label):
    return T4Case(args=(x0 & 0xFFFF, y0 & 0xFFFF, x1 & 0xFFFF, y1 & 0xFFFF), label=label)


def test_line():
    cases = [
        _case(5, 5, 5, 20, 'vline down'),
        _case(5, 20, 5, 5, 'vline up'),
        _case(3, 7, 30, 7, 'hline right'),
        _case(30, 7, 3, 7, 'hline left'),
        _case(0, 0, 20, 5, 'shallow'),
        _case(20, 5, 0, 0, 'shallow rev'),
        _case(0, 0, 5, 20, 'steep'),
        _case(5, 20, 0, 0, 'steep rev'),
        _case(0, 10, 20, 0, 'shallow up'),
        _case(10, 0, 0, 20, 'steep neg'),
        _case(4, 4, 4, 4, 'point'),
        _case(0, 0, 10, 10, 'diag'),
    ]
    t4spec.run_spec(
        SRC, 'Line_', 0x34ad0, cases,
        out_regs=(),
        stubs=[
            T4Stub(HLINE_ADDR, log_regs=("eax", "edx", "ebx")),
            T4Stub(VLINE_ADDR, log_regs=("eax", "edx", "ebx")),
        ],
        watch=WATCH,
        init_emu=init_emu,
    )


def test_t3_files_match():
    pass
