import os

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_34060', 'dpmi_get_free_memory_kb_reference.c')

SEGREAD = 0x30e57
INT386X = 0x30e7f


def test_t3_files():
    t4spec.assert_t3_matches(path('src/mod_34060'), [])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_34060'), ['dpmi_get_free_memory_kb_reference.c'])


def test_dpmi_get_free_memory_kb():
    def int386x_fn(e, log):
        log(e.reg("eax"), e.reg("edx"), e.reg("ebx"), e.reg("ecx"))
        return 0

    t4spec.run_spec(
        SRC, 'DpmiGetFreeMemoryKB_', 0x34060,
        cases=[T4Case(args=(), label='basic')],
        stubs=[T4Stub(SEGREAD, log_regs=('eax',)),
               T4Stub(INT386X, log_regs=('eax', 'edx', 'ebx', 'ecx'), fn=int386x_fn)],
        out_regs=('eax',),
    )
