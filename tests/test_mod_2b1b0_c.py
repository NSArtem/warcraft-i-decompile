import os
import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_2b1b0', 'terrain_walk_region_reference.c')

W, H, Y, CB, TBL, X = 0x5a33c, 0x5a340, 0x5a344, 0x5a348, 0x5a34c, 0x5a350

BUF = {}


def _init(emu):
    BUF['tbl'] = emu.alloc(0x4000, 16)


def test_t3_files_still_match():
    files = []
    if files:
        t4spec.assert_t3_matches(path('src/mod_2b1b0'), files)


def test_ref_files_still_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_2b1b0'), ['terrain_walk_region_reference.c'])


def _case(w, h, y, x, label):
    def setup(emu):
        import struct
        t = BUF['tbl']
        emu.write(t, bytes(range(256)) * 64)
        for a, v in ((W, w), (H, h), (Y, y), (X, x), (TBL, t), (CB, 0)):
            emu.write(a, struct.pack('<i', v & 0xFFFFFFFF if v < 0 else v))
    return T4Case(setup=setup, label=label)


def test_terrain_walk_region():
    cases = [
        _case(4, 4, 10, 10, 'inside'),
        _case(6, 6, 1, 1, 'neg'),
        _case(8, 8, 62, 62, 'over'),
        _case(0, 0, 5, 5, 'zero'),
        _case(5, 3, 2, 60, 'mixed'),
    ]
    # callback address is data; stub the target via a fixed code address
    stub_addr = 0x1000

    def setup_cb(c):
        old = c.setup

        def s(emu):
            import struct
            old(emu)
            emu.write(CB, struct.pack('<I', stub_addr))
        c.setup = s
        return c

    cases = [setup_cb(c) for c in cases]
    t4spec.run_spec(SRC, 'TerrainWalkRegion_', 0x2b1b0, cases,
                    out_regs=(),
                    watch=[(W, 0x20)],
                    stubs=[T4Stub(stub_addr, log_regs=('eax',))],
                    init_emu=_init)
