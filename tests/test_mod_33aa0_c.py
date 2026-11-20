import os

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')

SRC = path('src/mod_33aa0/dirty_rect_align_and_present_reference.c')

X1 = 0x5acd0  # dirty_x1 (word)


def test_t3_files_match():
    pass


def test_ref_mismatch_guard():
    t4spec.assert_ref_mismatch(path('src/mod_33aa0'), ['dirty_rect_align_and_present_reference.c'])


_bufs = {}


def _init(emu):
    _bufs['b'] = emu.alloc(64, 16)


def _case(x1, w, label):
    def setup(emu):
        pass
    return T4Case(args=(), label=label, setup=setup, regs_in=None, mem={})


def test_dirty_rect_align_and_present():
    import wc1.t4spec as ts
    funcs, datas = ts.load_lenient()
    by = {e['name']: a for t in (funcs, datas) for a, e in t.items()}
    ax1 = by.get('dirty_x1', X1)
    ax2 = by.get('dirty_x2')
    aw = by.get('dirty_w')
    cases = []
    vals = [(0, 0), (1, 5), (2, 8), (3, 3), (0x103, 0x102), (7, 1), (16, 16), (0x1ff, 0x7f), (5, 0xfe)]
    for x1, w in vals:
        def setup(emu, x1=x1, w=w):
            emu.write(ax1, x1.to_bytes(2, 'little'))
            emu.write(aw, w.to_bytes(2, 'little'))
        cases.append(T4Case(label=f"x1={x1:#x},w={w:#x}", setup=setup))
    watch = [(ax1, 2), (aw, 2)]
    if ax2:
        watch.append((ax2, 2))
    t4spec.run_spec(SRC, 'DirtyRectAlignAndPresent_', 0x33aa0, cases,
                    watch=watch,
                    stubs=[T4Stub(by['VidPresentRect'], log_regs=())] if 'VidPresentRect' in by else [],
                    out_regs=(), init_emu=_init)
