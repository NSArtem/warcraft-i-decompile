import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_3d260', 'draw_text_centered_reference.c')
T3_FILES = []
REF_FILES = ['draw_text_centered_reference.c']

BUF = {}
STATE = {'w': 0}


def _addr(*names):
    by = t4spec.by_link_lenient()
    for n in names:
        if n in by:
            return by[n]['addr']
    raise KeyError(names)


def _init(emu):
    BUF['bmp'] = emu.alloc(16, 16)
    BUF['font_a'] = emu.alloc(16, 16)
    BUF['font_b'] = emu.alloc(16, 16)
    BUF['str'] = emu.alloc(64, 16)


def test_t3_files_match():
    if not T3_FILES:
        pytest.skip("no T3 files") if False else None
        return
    t4spec.assert_t3_matches(path('src/mod_3d260'), T3_FILES)


def test_ref_files_still_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_3d260'), REF_FILES)


def _case(y, color, bmp_w, text_w, label, ghost=0):
    def setup(emu):
        emu.write(BUF['bmp'], struct.pack('<hh', bmp_w, 200))
        emu.write(BUF['str'], b'Hello\x00')
        emu.write(_addr('_cur_bitmap'), struct.pack('<I', BUF['bmp']))
        emu.write(_addr('_default_font'), struct.pack('<I', BUF['font_a']))
        emu.write(_addr('_cur_font'), struct.pack('<I', BUF['font_b']))
        STATE['w'] = text_w
    return T4Case(args=((ghost << 16) | (y & 0xFFFF), 0, color),
                  setup=setup, label=label)


def _fix_args(c):
    # string pointer is only known after init_emu
    inner = c.setup

    def setup(emu):
        inner(emu)
    c.setup = setup
    c.args = (c.args[0], BUF['str'], c.args[2])
    return c


def test_draw_text_centered():
    def init(emu):
        _init(emu)

    def tw(e, log):
        log(e.reg('eax'), e.reg('edx'))
        return STATE['w']

    stubs = [
        T4Stub(_addr('DrawText_'), log_regs=('eax', 'edx', 'ebx')),
        T4Stub(_addr('TextSetColorBase_'), log_regs=('eax',)),
        T4Stub(_addr('TextWidth_'), fn=tw),
    ]

    class Lazy(list):
        pass

    # cases built after buffers exist: run via init wrapper
    cases = []

    def init2(emu):
        init(emu)
        specs = [
            (10, 5, 320, 50, 'basic'),
            (0, 0, 320, 0, 'zero width'),
            (-3, 255, 320, 400, 'wider than bitmap (negative)'),
            (199, 7, 321, 51, 'odd diff'),
            (100, 1, 100, 99, 'diff one'),
            (50, 9, 640, 0x12345, 'width truncated to short'),
        ]
        for y, col, bw, tw_, lbl in specs:
            cases.append(_fix_args(_case(y, col, bw, tw_, lbl)))
        cases.append(_fix_args(_case(20, 3, 320, 70, 'garbage high bits', ghost=0xABCD)))

    init2(Emu_holder := type('H', (), {'alloc': None}) ) if False else None

    holder = {}

    def init_emu(emu):
        init2(emu)

    # run_spec calls init_emu before iterating cases; pass the live list
    t4spec.run_spec(SRC, 'DrawTextCentered_', 0x3d260, cases,
                    out_regs=(), stubs=stubs, init_emu=init_emu,
                    watch=[(_addr('_cur_font'), 4)])
