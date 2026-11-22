import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


def test_reference_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_33520'), ['crit_err_init_dialog_reference.c'])


def test_crit_err_init_dialog():
    def install(emu, log):
        log()
        # The dialog must clear the flag after the installer returns.
        emu.write(0x5555c, struct.pack('<H', 1))

    def case(label, color, installed, bitmap, message):
        return t4spec.T4Case(label=label, mem={
            0x62880: bytes([color]),
            0x5555c: struct.pack('<H', installed),
            0x55438: struct.pack('<I', bitmap),
            0x55560: struct.pack('<I', message),
        })

    t4spec.run_spec(
        'src/mod_33520/crit_err_init_dialog_reference.c',
        'CritErrInitDialog_',
        0x337d0,
        cases=[
            case('zero palette base', 0, 0, 0, 0x57ec4),
            case('ordinary palette base', 0x40, 1, 0x55574, 0x57ee4),
            case('neither offset wraps', 249, 0xffff, 0x5557c, 0x57ec4),
            case('only highlight wraps', 250, 0x8000, 0x55574, 0x57ee4),
            case('both offsets wrap', 253, 1, 0, 0x57ec4),
            case('maximum palette base', 255, 0, 0x5557c, 0x57ee4),
        ],
        watch=((0x55438, 4), (0x5555c, 2)),
        stubs=(
            t4spec.T4Stub(0x33764, log_regs=(), fn=install),
            t4spec.T4Stub(0x3d040, log_regs=('eax', 'edx', 'ebx', 'ecx')),
            t4spec.T4Stub(0x3d190, log_regs=('eax', 'edx', 'ebx', 'ecx')),
            t4spec.T4Stub(0x3d260, log_regs=('eax', 'edx', 'ebx')),
            t4spec.T4Stub(0x3d2b0, log_regs=('eax', 'edx', 'ebx', 'ecx')),
        ),
        out_regs=(),
    )
