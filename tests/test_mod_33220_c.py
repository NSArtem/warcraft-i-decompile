import os
import pytest

from wc1 import t4spec, path
from wc1.t4spec import T4Stub, T4Case

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_33220', 'palette_cycles_clear_reference.c')
PC_ADDR = 0x334fc


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_33220'), [])


def test_reference_still_mismatches():
    t4spec.assert_ref_mismatch(path('src/mod_33220'), ['palette_cycles_clear_reference.c'])


def test_palette_cycles_clear():
    pc = t4spec.by_link_lenient()['_palette_cycles']['addr']

    def fill(emu):
        emu.write(pc, bytes([(i * 37 + 1) & 0xFF for i in range(0xc0)]))

    cases = [T4Case(args=(), setup=fill, label="clear")]
    t4spec.run_spec(SRC, 'PaletteCyclesClear_', PC_ADDR, cases,
                    out_regs=(), watch=[(pc, 0xc0)])
