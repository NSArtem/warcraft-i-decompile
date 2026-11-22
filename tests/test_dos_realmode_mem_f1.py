import os

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')

MEMSET = 0x30c50
INT386 = 0x349ca


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/dos_realmode_mem'),
                             ['real_mode_alloc.c', 'real_mode_free.c',
                              'real_mode_int.c', 'real_mode_resize.c'])


def test_reference_still_mismatches():
    t4spec.assert_ref_mismatch(path('src/dos_realmode_mem'),
                               ['real_mode_get_vector_reference.c'])


def test_real_mode_get_vector():
    def int386_fn(e, log):
        # in regs: eax=intno, edx=in, ebx=out
        intno = e.reg("eax")
        inp = e.reg("edx")
        out = e.reg("ebx")
        ax = int.from_bytes(e.read(inp, 2), "little")
        bl = e.read(inp + 4, 1)[0]
        log(intno, ax, bl)
        # fill output: ecx at +8 (dword), edx at +0xc? use distinct pattern
        e.write(out + 8, (0x11223344 + bl).to_bytes(4, "little"))
        e.write(out + 0xc, (0xAABB0000 + bl * 0x101).to_bytes(4, "little"))
        return 0

    cases = [T4Case(args=(v,), label=f"intno{v:#x}")
             for v in (0, 1, 8, 0x1c, 0x21, 0x33, 0x7f, 0xff)]
    t4spec.run_spec(
        'src/dos_realmode_mem/real_mode_get_vector_reference.c',
        'RealModeGetVector_', 0x23e10, cases,
        stubs=[T4Stub_memset(), t4spec.T4Stub(INT386, fn=int386_fn)],
        out_regs=("eax", "edx"),
    )


def T4Stub_memset():
    def fn(e, log):
        dst = e.reg("eax")
        c = e.reg("edx") & 0xff
        n = e.reg("ebx")
        log(c, n)
        e.write(dst, bytes([c]) * n)
        return dst
    return t4spec.T4Stub(MEMSET, fn=fn)
