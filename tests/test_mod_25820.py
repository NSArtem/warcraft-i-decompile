import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


SRC = 'src/mod_25820'
# Give every speed a distinct reload value across the three tables.
DELAYS = {
    0x5325c: struct.pack('<5H', 30, 20, 10, 5, 2),
    0x53266: struct.pack('<5H', 11, 7, 4, 3, 1),
    0x53270: struct.pack('<5H', 13, 9, 6, 4, 2),
}
KEY_WORDS = (0x5a962, 0x5a964, 0x5a966, 0x5a96a, 0x5a96e,
             0x5a972, 0x5a974, 0x5a976, 0x5a9c2, 0x5a9c6,
             0x5a9c8, 0x5a9cc)


def _word(value):
    return struct.pack('<H', value & 0xffff)


def _dword(value):
    return struct.pack('<I', value & 0xffffffff)


def _delta_storage(watch, *globals_to_watch):
    storage = {}

    def init_emu(emu):
        storage['base'] = emu.alloc(8, 4)
        watch[:] = [(storage['base'], 8), *globals_to_watch]

    def case(label, mem, dx, dy, alias=False):
        # Capture the shared storage; run_spec allocates it before case setup.
        def setup(emu):
            emu.write(storage['base'], struct.pack('<hHhH', dx, 0xa55a, dy, 0x5aa5))

        pending.append((label, mem, setup, alias))

    pending = []
    cases = []

    def initialize(emu):
        init_emu(emu)
        base = storage['base']
        cases[:] = [
            t4spec.T4Case(args=(base, base if alias else base + 4),
                          mem=mem, setup=setup, label=label)
            for label, mem, setup, alias in pending
        ]

    return cases, case, initialize


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_25820'), ['map_scroll_from_mouse_edges.c', 'map_scroll_set_mouse_repeat.c', 'map_scroll_update_without_edges_reference.c'])


def test_reference_near_misses():
    t4spec.assert_ref_mismatch(path('src/mod_25820'), ['map_scroll_add_input_deltas_reference.c', 'map_scroll_apply_deltas_reference.c', 'map_scroll_filter_mouse_deltas_reference.c'])


def test_map_scroll_add_input_deltas():
    watch = []
    cases, add, init_emu = _delta_storage(watch, (0x53284, 4))

    def case(label, *, count=1, speed=0, phase=0, locked=0, position_key=0,
             x=192, y=100, keys=(), dx=7, dy=-11, alias=False):
        mem = dict(DELAYS)
        mem.update({addr: _word(0x8000 if addr in keys else 0) for addr in KEY_WORDS})
        mem.update({
            0x53284: _word(count) + _word(phase),
            0x532c4: _dword(speed),
            0x59426: struct.pack('<Hhh', 0xa639, x, y),
            0x59650: _word(locked),
            0x5a936: _word(position_key),
        })
        add(label, mem, dx, dy, alias)

    case('countdown holds off active input', count=2, keys=KEY_WORDS, position_key=1, x=224)
    case('zero countdown underflows without reload', count=0, phase=3, keys=KEY_WORDS)
    for speed in range(5):
        case(f'reload speed {speed}', speed=speed)
    for key in KEY_WORDS:
        case(f'independent key {key:#x}', keys=(key,))
    case('same-direction keys coalesce', keys=(0x5a9cc, 0x5a974, 0x5a976))
    case('opposites cancel', keys=KEY_WORDS)
    case('word deltas wrap', keys=(0x5a976,), dx=32767, dy=32767)
    case('aliased deltas accumulate both diagonal steps', keys=(0x5a976,), alias=True)
    case('position key off', x=144, y=148)
    case('locked still processes directional keys and toggles phase', locked=0x100,
         position_key=1, keys=(0x5a974,), x=144, y=148)
    case('nonzero phase toggles off', phase=0x8000, position_key=1, x=144, y=148)
    for x, y in ((192, 100), (177, 115), (176, 116), (175, 117),
                 (209, 83), (-32768, 32767), (32767, -32768)):
        case(f'position offsets at {x},{y}', position_key=0x100, x=x, y=y,
             keys=(0x5a966,))

    t4spec.run_spec(f'{SRC}/map_scroll_add_input_deltas_reference.c',
                    'MapScrollAddInputDeltas_', 0x25820, cases,
                    watch=watch, out_regs=(), init_emu=init_emu)


def test_map_scroll_filter_mouse_deltas():
    watch = []
    cases, add, init_emu = _delta_storage(watch, (0x5a0e0, 2))

    def case(label, count, speed, initial, repeat, alias=False):
        mem = dict(DELAYS)
        mem.update({0x5a0e0: _word(count), 0x532c0: _dword(speed),
                    0x5a0e4: bytes((initial, repeat))})
        add(label, mem, -17, 29, alias)

    case('one tick left still suppresses deltas', 1, 0, 1, 1)
    case('multiple ticks left ignore flags', 4, 1, 0, 0)
    case('negative countdown is active', -1, 2, 1, 1)
    case('signed boundary wraps', -32768, 3, 1, 1)
    case('neither flag clears aliased deltas', 0, 4, 0, 0, alias=True)
    for speed in range(5):
        case(f'initial speed {speed}', 0, speed, 0x80, 0)
        case(f'repeat speed {speed}', 0, speed, 0, 0x80)
        case(f'repeat takes precedence at speed {speed}', 0, speed, 1, 1)

    t4spec.run_spec(f'{SRC}/map_scroll_filter_mouse_deltas_reference.c',
                    'MapScrollFilterMouseDeltas_', 0x25970, cases,
                    watch=watch, out_regs=(), init_emu=init_emu)


def _read_deltas(emu):
    return tuple(struct.unpack('<h', emu.read(emu.reg(reg), 2))[0]
                 for reg in ('eax', 'edx'))


def _write_deltas(emu, dx, dy):
    emu.write(emu.reg('eax'), _word(dx))
    emu.write(emu.reg('edx'), _word(dy))


def test_map_scroll_apply_deltas():
    filtered = (0, 0)
    augmented = (0, 0)

    def filter_deltas(emu, log):
        edge = struct.unpack('<H', emu.read(0x5a0e2, 2))[0]
        log(*_read_deltas(emu), edge)
        _write_deltas(emu, *filtered)

    def add_input(emu, log):
        log(*_read_deltas(emu))
        _write_deltas(emu, *augmented)

    def case(dx, dy, buttons, after_filter, after_input, zero_cell=False):
        shapes = bytearray((8, 9, 14, 10, 0, 13, 12, 11, 7))
        if zero_cell:
            shapes[(dy + 1) * 3 + dx + 1] = 0

        def setup(_emu):
            nonlocal filtered, augmented
            filtered, augmented = after_filter, after_input

        return t4spec.T4Case(
            args=(dx, dy), regs_in={'ebx': 0}, setup=setup,
            mem={0x5327a: bytes(shapes), 0x59520: _word(0xbe42),
                 0x5942e: _word(buttons), 0x5a0e2: _word(0xffff)},
            label=f'edge=({dx},{dy}) buttons={buttons:#x} filter={after_filter} input={after_input}',
        )

    cases = [case(dx, dy, 0, (0, 0), (dx, dy))
             for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
    cases.extend([
        case(-1, 1, 0x100, (14, -23), (-2, 3)),
        case(1, -1, 0, (14, -23), (-32768, 32767)),
        case(1, 1, 0, (0, 0), (32767, -32768)),
        case(0, 0, 0, (0, 0), (-5, 6)),
        case(-1, -1, 1, (0, 0), (2, 3), zero_cell=True),
    ])
    stubs = [
        t4spec.T4Stub(0x25970, log_regs=(), fn=filter_deltas),
        t4spec.T4Stub(0x25820, log_regs=(), fn=add_input),
        *(t4spec.T4Stub(addr, log_regs=('eax',))
          for addr in (0x125c4, 0x12620, 0x12688, 0x126e4)),
    ]
    t4spec.run_spec(f'{SRC}/map_scroll_apply_deltas_reference.c',
                    'MapScrollApplyDeltas_', 0x259d8, cases, stubs=stubs,
                    watch=[(0x5a0e2, 2)], out_regs=('eax',))


def test_map_scroll_update_without_edges():
    def rewrite_shape(emu, log):
        addr = emu.reg('eax')
        value = struct.unpack('<I', emu.read(addr, 4))[0]
        log(value)
        emu.write(addr, _dword(value ^ 0x81234567))

    for shape in (0, 0x42, 0xfedc8080):
        t4spec.run_spec(f'{SRC}/map_scroll_update_without_edges_reference.c',
                        'MapScrollUpdateWithoutEdges_', 0x25b4c,
                        [t4spec.T4Case(label=f'initial shape {shape:#x}')],
                        stubs=[t4spec.T4Stub(0x259d8, ret=shape, log_regs=('eax', 'edx')),
                               t4spec.T4Stub(0x2df9c, log_regs=(), fn=rewrite_shape)],
                        out_regs=('eax',))
