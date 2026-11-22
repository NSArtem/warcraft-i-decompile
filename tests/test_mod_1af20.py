import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = 'src/mod_1af20'
UNIT_ARRAY = 0x59640
UNIT_SIZE = 0x5c
UNIT_COUNT = 200
CHAT_LEN = 0x59650
CHAT_TEXT = 0x59652
CHEAT_FLAGS = 0x51214


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_1af20'), ['game_screen_cancel_or_place.c', 'map_center_on_tile.c', 'map_center_on_unit.c', 'map_free_buffers.c', 'map_issue_target_order.c'])


def test_reference_near_misses():
    t4spec.assert_ref_mismatch(path('src/mod_1af20'), ['game_screen_handle_chat_key_reference.c', 'game_screen_restore_input_reference.c', 'game_screen_schedule_input_restore_reference.c', 'map_find_start_tile_reference.c', 'map_init_buffers_reference.c'])


def test_map_find_start_tile():
    mem = {}
    watch = []

    def init_emu(e):
        mem['units'] = e.alloc(UNIT_COUNT * UNIT_SIZE, 16)
        mem['xy'] = e.alloc(8, 4)
        watch[:] = [(mem['xy'], 8)]

    def case(label, rows, alias_outputs=False):
        def setup(e):
            units = bytearray(UNIT_COUNT * UNIT_SIZE)
            for i in range(UNIT_COUNT):
                struct.pack_into('<H', units, i * UNIT_SIZE + 0x10, 1)
            for i, flags, owner, kind, x, y in rows:
                off = i * UNIT_SIZE
                struct.pack_into('<Hhh', units, off + 8, 0xa55a, x, y)
                struct.pack_into('<H', units, off + 0x10, flags)
                units[off + 0x1b] = kind
                units[off + 0x1e] = owner
            e.write(mem['units'], bytes(units))
            e.write(UNIT_ARRAY, struct.pack('<I', mem['units']))
            e.write(mem['xy'], struct.pack('<ii', 0x12345678, -987654))

        # The heap addresses are only available after init_emu runs.
        c = T4Case(label=label)

        def prepare(e):
            setup(e)
            c.args = (mem['xy'], mem['xy'] + (0 if alias_outputs else 4))

        c.setup = prepare
        return c

    t4spec.run_spec(
        f'{SRC}/map_find_start_tile_reference.c', 'MapFindStartTile_', 0x1b12c,
        cases=[
            case('no eligible unit', [(4, 0, 1, 0x28, 11, 22)]),
            case('first fallback; 0x27 and 0x2a are not preferred', [
                (0, 0x8008, 0, 0x27, -32768, 32767),
                (1, 0, 0, 0x2a, 17, -19), (199, 0, 0, 0xff, 9, 6),
            ]),
            case('last-slot preferred; skip every masked bit and nonzero owner', [
                (0, 0, 0, 0x10, 3, 4), (1, 1, 0, 0x28, 5, 6),
                (2, 2, 0, 0x28, 7, 8), (3, 4, 0, 0x28, 9, 10),
                (4, 0x200, 0, 0x29, 11, 12), (5, 0, 255, 0x28, 13, 14),
                (199, 0, 0, 0x29, -123, -456),
            ]),
            case('first preferred wins; aliased outputs keep y', [
                (2, 0, 0, 0x28, 55, -66), (3, 0, 0, 0x29, 77, 88),
            ], alias_outputs=True),
            case('last slot is the only fallback', [(199, 0, 0, 0x2a, 63, 0)]),
        ],
        watch=watch, out_regs=(), init_emu=init_emu,
    )


def test_map_init_buffers():
    sizes = (0x4000, 0x2000, 0x4000, 0x2000, 0x2000, 0x2000,
             0x10000, 0x10000, 0xed8, 0x47e0)
    buffers = []
    next_alloc = 0
    watch = []
    cases = [
        T4Case(args=(0,), label='fresh map, fog obscured'),
        T4Case(args=(0,), label='fresh demo map, no fog obscure call'),
        T4Case(label='restore stream, signed scroll and advanced cursor'),
    ]

    def init_emu(e):
        buffers.extend(e.alloc(n, 16) for n in sizes)
        cases[2].args = (e.alloc(0xa000, 16),)
        watch[:] = [
            (0x58570, 0x20), (0x59510, 4), (0x59518, 4), (0x59520, 2),
            (0x59640, 8), (0x5a7e0, 2), (0x5ac1c, 0x12),
            (0x500ce, 6),
        ] + [(buffers[i], sizes[i]) for i in (2, 4, 8, 9)]

    for c, race, demo, x, y in zip(cases, (0, 0xffff, 1), (0, 2, 0),
                                    (125, 0xffff, 0x8000), (63, 0x8001, 0xfffe)):
        c.mem = {
            0x50088: struct.pack('<H', race),
            0x500ce: struct.pack('<8H', 0xa55a, x, y, 0x101, 0x202, 0x8303, 0x4404, 0x5505),
            0x5152c: struct.pack('<H', demo),
        }

    def setup(e):
        nonlocal next_alloc
        next_alloc = 0
        for addr, n in watch:
            if addr != 0x500ce:
                e.write(addr, b'\xa5' * n)

    for c in cases:
        c.setup = setup

    def alloc(e, log):
        nonlocal next_alloc
        # One ten-allocation sequence per side of the differential pair.
        p = buffers[next_alloc % len(sizes)]
        next_alloc += 1
        log(e.reg('eax'))
        return p

    def near_fill(e, log):
        dst, value, count = (e.reg(r) for r in ('eax', 'edx', 'ebx'))
        log(dst, value, count)
        e.write(dst, bytes([value & 0xff]) * count)
        return dst

    def far_fill(e, log):
        dst, selector, value, count = (e.reg(r) for r in ('eax', 'edx', 'ebx', 'ecx'))
        log(dst, selector & 0xffff, value, count)
        e.write(dst, bytes([value & 0xff]) * count)
        return dst

    def read_save(e, log):
        dst, count, pos = (e.reg(r) for r in ('eax', 'edx', 'ebx'))
        log(dst, count, pos)
        return pos + count

    t4spec.run_spec(
        f'{SRC}/map_init_buffers_reference.c', 'MapInitBuffers_', 0x1b198,
        cases=cases, init_emu=init_emu, watch=watch, out_regs=('eax',),
        stubs=[
            T4Stub(0x25b6c, log_regs=('eax',)),
            T4Stub(0x25b80, log_regs=('eax',)),
            T4Stub(0x32558, log_regs=('eax',), fn=alloc),
            T4Stub(0x30c50, log_regs=('eax', 'edx', 'ebx'), fn=near_fill),
            T4Stub(0x31870, log_regs=('eax', 'edx')),
            T4Stub(0x32740, log_regs=('eax', 'edx')),
            T4Stub(0x33150, log_regs=('eax', 'edx', 'ebx')),
            T4Stub(0x123f0, log_regs=()),
            T4Stub(0x249a4, log_regs=('eax', 'edx', 'ebx'), fn=read_save),
            T4Stub(0x24a68, log_regs=('eax',)),
            T4Stub(0x33b41, log_regs=('eax', 'edx', 'ebx', 'ecx'), fn=far_fill),
            T4Stub(0x12438, log_regs=()),
            T4Stub(0x1274c, log_regs=('eax', 'edx')),
        ],
    )


def test_game_screen_restore_input():
    t4spec.run_spec(
        f'{SRC}/game_screen_restore_input_reference.c', 'GameScreenRestoreInput_', 0x1b43c,
        cases=[T4Case(label='disable input mode then reinitialize screen input')],
        out_regs=(), stubs=[
            T4Stub(0x25b80, log_regs=('eax',)),
            T4Stub(0x1a328, log_regs=()),
        ],
    )


def test_game_screen_schedule_input_restore():
    t4spec.run_spec(
        f'{SRC}/game_screen_schedule_input_restore_reference.c', 'GameScreenScheduleInputRestore_', 0x1b560,
        cases=[T4Case(mem={0x59414: struct.pack('<I', old)}, label=label)
               for old, label in ((0, 'install callback'), (0x1a328, 'replace callback'))],
        out_regs=(), watch=[(0x59414, 4)], stubs=[T4Stub(0x25b80, log_regs=('eax',))],
    )


def test_game_screen_handle_chat_key():
    def case(label, key, text=None, ch=0, modifier=0, handled=0):
        line = b'' if text is None else text + b'_\x00'
        n = 0 if text is None else len(text) + 1
        # Seed nonzero trailing bytes to expose wrong-index stores.
        c = T4Case(label=label, mem={
            CHAT_LEN: struct.pack('<H', n),
            CHAT_TEXT: line.ljust(32, b'\xa5'),
            CHEAT_FLAGS: struct.pack('<I', 0x10203040),
        })
        return c, bytes(8) + bytes((key, 0, ch, modifier)), handled

    inputs = [
        case('inactive non-Enter', 0x1e, ch=0x61),
        case('Enter opens the editor', 0x1c),
        case('Enter closes empty editor', 0x1c, b''),
        case('Enter submits chat', 0x1c, b'hello'),
        case('Enter submits updated cheat flags', 0x1c, b'cheat', handled=1),
        case('backspace at minimum length', 0x0e, b''),
        case('backspace removes final character', 0x0e, b'ab'),
        case('reject nonzero modifier', 0x1e, b'ab', ch=0x61, modifier=1),
        case('reject below printable range', 0x1e, b'ab', ch=0x1f),
        case('accept space', 0x1e, b'ab', ch=0x20),
        case('accept upper boundary', 0x1e, b'x' * 28, ch=0x7f),
        case('reject above upper boundary', 0x1e, b'ab', ch=0x80),
        case('reject append at length cap', 0x1e, b'x' * 29, ch=0x61),
    ]
    handled = 0

    def init_emu(e):
        evt = e.alloc(12, 4)

        def setup_for(event, result):
            def setup(emu):
                nonlocal handled
                handled = result
                emu.write(evt, event)
            return setup

        for c, event, result in inputs:
            c.args = (evt,)
            c.setup = setup_for(event, result)

    def cstr(e, addr):
        value = e.cstr(addr, 64)
        return value.encode('latin-1') if isinstance(value, str) else bytes(value)

    def log_text(log, text, *args):
        # Compare contents, not stack addresses. Length disambiguates padding.
        padded = text + bytes((-len(text)) % 4)
        log(*args, len(text), *struct.unpack('<' + 'I' * (len(padded) // 4), padded))

    def process(e, log):
        flags = e.reg('edx')
        log_text(log, cstr(e, e.reg('eax')), struct.unpack('<I', e.read(flags, 4))[0])
        if handled:
            e.write(flags, struct.pack('<I', 0x89abcdef))
        return handled

    def send_chat(e, log):
        log_text(log, cstr(e, e.reg('eax')), e.reg('edx') & 0xffff)

    def concat(e, log):
        dst, src = e.reg('eax'), e.reg('edx')
        prefix, suffix = cstr(e, dst), cstr(e, src)
        log_text(log, prefix + b'\x00' + suffix)
        e.write(dst + len(prefix), suffix + b'\x00')
        return dst

    def prompt(e, log):
        log_text(log, cstr(e, e.reg('eax')), e.reg('edx'))

    t4spec.run_spec(
        f'{SRC}/game_screen_handle_chat_key_reference.c', 'GameScreenHandleChatKey_', 0x1b690,
        cases=[c for c, _, _ in inputs], init_emu=init_emu,
        watch=[(CHAT_LEN, 34), (CHEAT_FLAGS, 4)], out_regs=('eax',),
        stubs=[
            T4Stub(0x12b50, log_regs=('eax', 'edx'), fn=process),
            T4Stub(0x21c44, log_regs=('eax',)),
            T4Stub(0x21c68, log_regs=('eax', 'edx'), fn=send_chat),
            T4Stub(0x31feb, log_regs=('eax', 'edx'), fn=concat),
            T4Stub(0x2b67c, log_regs=('eax', 'edx'), fn=prompt),
        ],
    )
