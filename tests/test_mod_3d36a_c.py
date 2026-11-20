import os
import pytest
import struct

from wc1 import path, t4spec
from wc1.t4spec import T4Case

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_3d36a/vid_present_rect_reference.c')
_ST = {}


def test_t3_files_match():
    files = []
    if files:
        t4spec.assert_t3_matches(path('src/mod_3d36a'), files)


def test_ref_mismatch_guard():
    t4spec.assert_ref_mismatch(path('src/mod_3d36a'), ['vid_present_rect_reference.c'])


def _addr(name):
    bl = t4spec.by_link_lenient()
    for k in (name, '_' + name):
        if k in bl:
            return bl[k]['addr']
    raise KeyError(name)


def _init(emu):
    buf = emu.alloc(0x10000, 16)
    _ST['buf'] = buf
    emu.write(buf, bytes((i * 7 + 3) & 0xFF for i in range(0x10000)))
    try:
        emu.uc.mem_map(0xA0000, 0x10000)
    except Exception:
        pass
    emu.write(0xA0000, b'\x00' * 0x10000)


def _case(x, y, w, h, label):
    def setup(emu):
        emu.write(0x5A874, struct.pack('<I', _ST['buf']))
        emu.write(_addr('dirty_x1'), struct.pack('<h', x))
        emu.write(_addr('dirty_y1'), struct.pack('<h', y))
        emu.write(_addr('dirty_w'), struct.pack('<h', w))
        emu.write(_addr('dirty_h'), struct.pack('<h', h))
        emu.write(0xA0000, b'\x00' * 0x10000)
    return T4Case(setup=setup, label=label)


def test_vid_present_rect():
    cases = [
        _case(0, 0, 4, 1, 'min'),
        _case(8, 2, 16, 3, 'mid'),
        _case(100, 5, 32, 4, 'wide'),
        _case(0, 0, 320, 2, 'full width'),
    ]
    t4spec.run_spec(SRC, 'VidPresentRect_', 0x3d560, cases,
                    watch=[(0xA0000, 0x10000)], out_regs=(),
                    init_emu=_init)
