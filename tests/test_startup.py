import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


def test_startup_t3_matches():
    t4spec.assert_t3_matches(path('src/init'), ['load_config_file.c', 'load_modem_settings.c', 'load_preferences.c', 'parse_startup_option.c', 'print_usage_and_exit.c', 'process_command_line.c', 'save_file_in_exe_dir.c', 'save_modem_settings.c', 'save_preferences_on_exit.c'])


def test_startup_reference_near_miss():
    t4spec.assert_ref_mismatch(path('src/init'), ['print_exit_banner_reference.c'])


def test_print_exit_banner():
    banner = 0x18260
    stream = 0x555DE
    used_addr = 0x555E2
    flags_addr = 0x555EB
    size_addr = 0x555F2
    is_table = 0x583D4
    buffer_size = 256
    buf = None
    watch = []

    def init_emu(emu):
        nonlocal buf
        buf = emu.alloc(buffer_size, 16)
        watch[:] = [(stream, size_addr + 4 - stream), (buf, buffer_size)]

    def make_case(label, *, status=0, used=0, size=buffer_size - 8,
                  flags=0, accepted=None, text=None):
        mem = {
            used_addr: struct.pack('<I', used),
            flags_addr: bytes((flags, 0, 0, 0)),
            size_addr: struct.pack('<I', size),
        }
        if accepted is not None:
            table = bytearray(257)
            for c in accepted:
                table[(c + 1) & 0xFF] = 8
            mem[is_table] = bytes(table)
        if text is not None:
            mem[banner] = text

        def setup(emu):
            emu.write(stream, struct.pack('<I', buf + 8))
            emu.write(buf, b'\xA5' * buffer_size)

        return t4spec.T4Case(args=(status,), mem=mem, setup=setup, label=label)

    # Leave the shipped banner and classification table intact for these cases.
    cases = [
        make_case('nonzero status bypasses output', status=1),
        make_case('high-bit status bypasses output', status=0x80),
        make_case('shipped banner with available buffer space'),
        make_case('shipped banner with direct-output flag', flags=4),
    ]

    # Both implementations read this same data prefix. Including a NUL in
    # each replacement keeps all reads within the test string.
    text = b'A@?\n\xff\0'
    accepted = b'A\n\xff'
    cases += [
        make_case('buffered printable, marker, classified newline and wrapped index',
                  flags=0x20, text=text, accepted=accepted),
        make_case('two bytes left: first byte buffered, remainder delegated',
                  used=6, size=8, text=text, accepted=accepted),
        make_case('one byte left: all emitted bytes delegated',
                  used=7, size=8, text=text, accepted=accepted),
        make_case('zero bytes left: all emitted bytes delegated',
                  used=8, size=8, text=text, accepted=accepted),
        make_case('unsigned room subtraction wraps when used exceeds size',
                  used=9, size=8, text=text, accepted=accepted),
        make_case('empty banner still emits final newline', text=b'\0', accepted=b''),
    ]
    t4spec.run_spec(
        'src/init/print_exit_banner_reference.c', 'PrintExitBanner_', 0x1D854,
        cases, init_emu=init_emu, watch=watch, out_regs=(),
        stubs=[t4spec.T4Stub(0x33F90, log_regs=('eax', 'edx'))],
    )
