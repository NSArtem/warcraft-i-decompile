import os
import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_30bd0', 'vid_setup_backbuffer_reference.c')


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_30bd0'), [])


def test_reference_still_mismatches():
    t4spec.assert_ref_mismatch(path('src/mod_30bd0'), ['vid_setup_backbuffer_reference.c'])


def test_vid_setup_backbuffer():
    cases = [
        t4spec.T4Case(args=(v,), label="arg=%#x" % v)
        for v in (0, 1, 0x7f, 0x100, 0x1234, 0x8000, 0xffff)
    ]
    # high garbage in eax upper bits: arg is a 16-bit value
    cases.append(t4spec.T4Case(args=(0xABCD1234,), label="dirty upper"))
    t4spec.run_spec(
        SRC, 'VidSetupBackbuffer_', 0x30bd0, cases,
        stubs=[T4Stub(0x3b360, log_regs=("eax", "edx")),
               T4Stub(0x3b3a0, log_regs=())],
        out_regs=(),
    )
