import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

HEADER = 0x594E4
WIDTH = 0x59448
IMAGE_PTR = 0x594D4
CHUNK_PTR = 0x594D8
FIRST = 0x594D0
LAST = 0x594DC
PALETTE_ON = 0x594EA
PALETTE = 0x58F20
READ = 0x19020
STRIDE = 320


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/flic_decode'), ['flic_decode_frame.c', 'flic_read_bytes.c', 'flic_seek.c'])


def test_reference_near_misses():
    t4spec.assert_ref_mismatch(path('src/flic_decode'), ['flic_decode_chunk_reference.c', 'flic_decode_palette_chunk_reference.c'])


def test_flic_decode_palette_chunk():
    watch = []
    buffers = {}

    def init_emu(emu):
        buffers['chunk'] = emu.alloc(1024, 16)
        watch[:] = [(PALETTE, 768), (buffers['chunk'], 1024)]

    def read_chunk(emu, log):
        dst, count = emu.reg('eax'), emu.reg('edx') & 0xFFFF
        log(dst, count)
        if count == 0:
            return 0
        assert dst == buffers['chunk'] and count <= 1024
        # The fixture preloads the bytes a successful read makes available.
        return 1

    def upload_palette(emu, log):
        # cdecl: skip the return address; record only the three arguments.
        log(*struct.unpack('<III', emu.read(emu.reg('esp') + 4, 12)))
        return 0

    def case(label, payload, first, last, enabled, size=None):
        def setup(emu):
            chunk = buffers['chunk']
            emu.write(CHUNK_PTR, struct.pack('<I', chunk))
            emu.write(chunk, payload.ljust(1024, b'\xCC'))

        return T4Case(label=label, setup=setup, mem={
            HEADER: struct.pack('<IH', len(payload) + 6 if size is None else size, 4),
            FIRST: struct.pack('<i', first),
            LAST: struct.pack('<i', last),
            PALETTE_ON: struct.pack('<H', enabled),
            PALETTE: b'\xA5' * 768,
        })

    # Packet 1 fills indices 2 and 3; packet 2 skips index 4 and fills 5.
    sparse = bytes([2, 0, 2, 2, 0, 3, 4, 127, 128, 255, 1, 1, 252, 251, 7])
    full = b'\x01\x00\x00\x00' + bytes((i * 37 + 3) & 255 for i in range(768))
    t4spec.run_spec(
        'src/flic_decode/flic_decode_palette_chunk_reference.c',
        'FlicDecodePaletteChunk_', 0x19064,
        cases=[
            case('read failure; no upload even when enabled', b'', 0, 255, 1),
            case('first packet; inclusive bounds; VGA off', sparse, 2, 3, 0),
            case('second packet; relative skip; VGA on', sparse, 5, 5, 1),
            case('zero count means 256; full copy and upload', full, 0, 255, 1),
            case('payload read uses low 16 bits of size minus six', full, 255, 255, 0,
                 size=0x10000 + len(full) + 6),
            case('zero packets and empty copy range; upload still enabled',
                 b'\x00\x00', 1, 0, 1),
        ],
        watch=watch, init_emu=init_emu,
        stubs=[T4Stub(READ, log_regs=('eax', 'edx'), fn=read_chunk),
               T4Stub(0x331BE, log_regs=(), fn=upload_palette)],
    )


def test_flic_decode_chunk():
    watch = []
    buffers = {}
    scenario = {}

    def init_emu(emu):
        buffers['chunk'] = emu.alloc(128, 16)
        buffers['image'] = emu.alloc(4 * STRIDE, 16)
        watch[:] = [(HEADER, 6), (buffers['chunk'], 128),
                    (buffers['image'], 4 * STRIDE)]

    def read(emu, log):
        dst, count = emu.reg('eax'), emu.reg('edx') & 0xFFFF
        log(dst, count)
        if dst == HEADER:
            assert count == 6
            if scenario['header_fail']:
                return 0
            emu.write(dst, scenario['header'])
        elif dst == buffers['chunk']:
            assert count == scenario['payload_count'] and count <= 128
            if scenario['payload_fail']:
                return 0
            emu.write(dst, bytes(range(count)))
        else:
            offset = dst - buffers['image']
            row, remainder = divmod(offset, STRIDE)
            assert remainder == 0 and 0 <= row < scenario['height']
            assert count == scenario['width']
            if row == scenario['fail_row']:
                return 0
            emu.write(dst, bytes([0x30 + row]) * count)
        return 1

    def case(label, kind, *, size=19, width=9, height=3, header_fail=False,
             payload_fail=False, fail_row=None, palette_result=1):
        def setup(emu):
            scenario.update(header=struct.pack('<IH', size, kind),
                            payload_count=(size - 6) & 0xFFFF,
                            width=width, height=height, header_fail=header_fail,
                            payload_fail=payload_fail, fail_row=fail_row,
                            palette_result=palette_result)
            emu.write(CHUNK_PTR, struct.pack('<I', buffers['chunk']))
            emu.write(IMAGE_PTR, struct.pack('<I', buffers['image']))
            emu.write(buffers['chunk'], b'\xCC' * 128)
            emu.write(buffers['image'], b'\xA5' * (4 * STRIDE))

        return T4Case(label=label, setup=setup, mem={
            HEADER: b'\xEF' * 6,
            WIDTH: struct.pack('<HH', width, height),
        })

    def decode_palette(emu, log):
        log()
        return scenario['palette_result']

    cases = [
        case('header read fails before dispatch', 16, header_fail=True),
        case('palette success', 4),
        case('palette failure propagated', 4, palette_result=0),
        case('raw rows use 320-byte pitch, not width', 16),
        case('raw rows stop after second read fails', 16, fail_row=1),
        case('raw zero-height skips row reads', 16, height=0),
        case('seek takes full dword size minus six', 18, size=0x12340019),
        case('seek accepts zero displacement', 18, size=6),
    ]
    for kind in (7, 12, 15):
        cases.extend([
            case(f'type {kind}: payload success and decoder dispatch', kind,
                 size=0x10013 if kind == 7 else 19),
            case(f'type {kind}: payload failure prevents decoder call', kind,
                 payload_fail=True),
        ])
    for kind in (0, 3, 5, 8, 11, 13, 14, 17, 19, 0xFFFF):
        cases.append(case(f'unsupported type {kind}', kind))

    t4spec.run_spec(
        'src/flic_decode/flic_decode_chunk_reference.c',
        'FlicDecodeChunk_', 0x19174, cases=cases, watch=watch, init_emu=init_emu,
        stubs=[
            T4Stub(READ, log_regs=('eax', 'edx'), fn=read),
            T4Stub(0x19064, log_regs=(), fn=decode_palette),
            T4Stub(0x102A4, ret=2, log_regs=('eax', 'edx')),
            T4Stub(0x10312, ret=3, log_regs=('eax', 'edx', 'ebx')),
            T4Stub(0x1025C, ret=4, log_regs=('eax', 'edx', 'ebx', 'ecx')),
            T4Stub(0x19048, log_regs=('eax', 'edx')),
        ],
    )
