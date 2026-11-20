import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC_DIR = path('src/mod_1c020')
REFS = ['credit_draw_a_reference.c', 'credit_draw_b_reference.c',
        'credit_draw_c_reference.c', 'credit_draw_d_reference.c']

FRAMES = (0, 1, 7, 0x7F, 0xFF)
PTRS = (0x12345678, 0x00401000)


def test_t3_files_still_match():
    t4spec.assert_t3_matches(SRC_DIR, [])


def test_reference_files_still_mismatch():
    t4spec.assert_ref_mismatch(SRC_DIR, REFS)


def _addr(link):
    return t4spec.by_link_lenient()[link]["addr"]


def _stubs():
    return (
        T4Stub(_addr("LayerInvalidate_"), log_regs=("eax",)),
        T4Stub(_addr("GrpFrameBitmap_"), log_regs=("eax", "edx", "ebx")),
        T4Stub(_addr("ScreenUpdate_"), log_regs=()),
    )


def _cases(ptr_addr):
    out = []
    for p in PTRS:
        for f in FRAMES:
            out.append(T4Case(args=(f,), mem={ptr_addr: struct.pack("<I", p)},
                              label=f"ptr={p:#x},frame={f}"))
    return out


def _run(src, name, addr, ptr_addr):
    t4spec.run_spec(path('src/mod_1c020', src), name, addr, _cases(ptr_addr),
                    stubs=_stubs(), out_regs=())


def test_credit_draw_a():
    _run('credit_draw_a_reference.c', 'CreditDrawA_', 0x1c1dc, 0x59860)


def test_credit_draw_b():
    _run('credit_draw_b_reference.c', 'CreditDrawB_', 0x1c214, 0x59858)


def test_credit_draw_c():
    _run('credit_draw_c_reference.c', 'CreditDrawC_', 0x1c24c, 0x5985c)


def test_credit_draw_d():
    _run('credit_draw_d_reference.c', 'CreditDrawD_', 0x1c284, 0x59854)
