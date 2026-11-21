import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM',
)

SRC_DIR = path('src/mod_33520')
CEI = path('src/mod_33520', 'crit_err_install.c')


def test_t3_files_match():
    t4spec.assert_t3_matches(
        SRC_DIR,
        ['crit_err_lock_start.c', 'crit_err_handler.c', 'crit_err_lock_end.c', 'crit_err_install.c'],
    )


def test_crit_err_install():
    def mk(init_inst, init_flag, init_np, label):
        def setup(emu):
            emu.write(0x5555c, struct.pack('<h', init_inst))
            emu.write(0x61ea0, struct.pack('<hh', init_flag, init_np))
        return T4Case(args=(), setup=setup, label=label)

    cases = [
        mk(0, 7, 9, "from_zero_installed"),
        mk(42, -1, 123, "from_nonzero_installed"),
    ]
    stubs = [
        T4Stub(0x312f0, log_regs=("eax", "edx")),
        T4Stub(0x3cf5e, log_regs=("eax",)),
    ]
    t4spec.run_spec(
        CEI, 'CritErrInstall_', 0x33764, cases,
        stubs=stubs, watch=[(0x5555c, 2), (0x61ea0, 4)], out_regs=(),
    )
