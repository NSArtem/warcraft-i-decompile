import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


def test_reference_near_miss():
    t4spec.assert_ref_mismatch(path('src/mod_12c70'), ['net_process_received_packet_reference.c'])


def test_net_process_received_packet():
    selector_storage = 0x52582
    request_buffer = 0x585A0
    send_state = 0x58D9C
    watch = []
    packet = None
    records = []
    record_lengths = (0, 17, 0xFF)
    record_size = 0x104

    def init_emu(emu):
        nonlocal packet
        packet = emu.alloc(16, 16)
        records[:] = [emu.alloc(record_size, 16) for _ in record_lengths]
        watch[:] = [(packet, 16), (selector_storage, 4),
                    (request_buffer, 8), (send_state, 6)]
        watch.extend((record, record_size) for record in records)

    def lookup(emu, log):
        seq = emu.reg('eax')
        log(seq)
        slot = {10: 0, 12: 1, 13: 2, 0xFFFE: 2}.get(seq)
        return 0 if slot is None else records[slot]

    def case(label, raw_type, seq, expected=0x1234, sent=0, selector=0):
        packet_bytes = struct.pack('<BBH12s', 0x5A, raw_type, seq, b'packet-tail!')

        def setup(emu):
            emu.write(packet, packet_bytes)
            for record, length in zip(records, record_lengths):
                emu.write(record, b'\x91\x82\x73\x64' + bytes([length]) +
                          b'\xA7' * (record_size - 5))

        return t4spec.T4Case(
            mem={selector_storage: struct.pack('<Hh', 0xA55A, selector),
                 request_buffer: b'\x11\x22\x33\x44\xA5\xB6\xC7\xD8',
                 send_state: struct.pack('<HHH', sent, expected, 0xD16E)},
            setup=setup, label=label)

    cases = []
    for kind in (1, 2, 4, 5, 6, 7, 8):
        for label, seq in (('older', 0x1233), ('expected', 0x1234),
                           ('successor', 0x1235), ('gap', 0x1236)):
            cases.append(case(f'type {kind}: {label}', kind | 0x80, seq))

    cases.extend([
        case('unknown type below table', 0x80, 0x1234),
        case('unknown type above table', 0x89, 0x1234),
        case('largest masked type', 0xBF, 0x1234),
        case('selector zero matches, flags stay set', 0x41, 0x1234),
        case('selector one matches, resend is suppressed', 0xC3, 10, sent=14, selector=1),
        case('selector zero mismatches one', 0x41, 0x1234, selector=1),
        case('selector one mismatches zero', 0xC1, 0x1234),
        case('negative selector passes', 0xC1, 0x1234, selector=-1),
        case('ordinary expected sequence wraps', 1, 0xFFFF, expected=0xFFFF),
        case('ordinary zero is not successor of FFFF', 1, 0, expected=0xFFFF),
        case('ordinary FFFF is successor of FFFE', 1, 0xFFFF, expected=0xFFFE),
        case('type 8 expected FFFF does not advance', 8, 0xFFFF, expected=0xFFFF),
        case('type 8 zero is not successor of FFFF', 8, 0, expected=0xFFFF),
        case('type 8 FFFF is successor of FFFE', 8, 0xFFFF, expected=0xFFFE),
        case('resend mixed hits and miss', 0x83, 10, sent=14),
        case('resend all misses', 3, 20, sent=23),
        case('resend starts at exclusive limit', 3, 14, sent=14),
        case('resend starts above limit', 3, 15, sent=14),
        case('resend stops at FFFF without wrapping', 3, 0xFFFE, sent=0xFFFF),
    ])

    # init_emu allocates the packet before run_spec starts executing cases.
    def init_cases(emu):
        init_emu(emu)
        for entry in cases:
            entry.args = (packet,)

    t4spec.run_spec(
        'src/mod_12c70/net_process_received_packet_reference.c',
        'NetProcessReceivedPacket_', 0x12DEC, cases,
        watch=watch, out_regs=('eax',), init_emu=init_cases,
        stubs=(t4spec.T4Stub(0x12D2C, log_regs=('eax',), fn=lookup),
               t4spec.T4Stub(0x20A50, log_regs=('eax', 'edx'))),
    )
