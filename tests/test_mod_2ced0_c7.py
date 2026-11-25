import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = 'src/mod_2ced0/'
UNIT_ARRAY = 0x59640
OBJECT_ARRAY = 0x59644
UNIT_STRIDE = 0x5c
OBJECT_STRIDE = 0x26
UNIT_COUNT = 200
OBJECT_COUNT = 100


def u16(value):
    return struct.pack('<H', value & 0xffff)


def u32(value):
    return struct.pack('<I', value)


def unit_at(base, index):
    return base + UNIT_STRIDE * index


def unit_records(flags=1):
    data = bytearray(b'\xa5' * (UNIT_COUNT * UNIT_STRIDE))
    for offset in range(0, len(data), UNIT_STRIDE):
        struct.pack_into('<H', data, offset + 0x10, flags)
    return data


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_2ced0'), ['unit_finalize_gone.c'])


def test_reference_near_misses():
    t4spec.assert_ref_mismatch(path('src/mod_2ced0'), ['map_pick_order_target_reference.c', 'simulation_tick_reference.c', 'units_update_visibility_reference.c'])


def test_units_update_visibility():
    watch = []
    layout = {}
    sizes = 0x51abc
    cheats = 0x51214

    def init_emu(e):
        layout['units'] = e.alloc(UNIT_COUNT * UNIT_STRIDE, 16)
        watch[:] = [(layout['units'], UNIT_COUNT * UNIT_STRIDE)]

    def fog(e, log):
        xy, size, mask, expected = (e.reg(r) for r in ('eax', 'edx', 'ebx', 'ecx'))
        log(xy, size, mask & 0xffff, expected & 0xffff)
        selector = struct.unpack('<h', e.read(xy, 2))[0]
        bit = 1 if (mask & 0xffff) == 0x001f else 2
        return 0x10001 if selector & bit else 0x10000

    def setup(e):
        data = unit_records()
        rows = [
            (0, 0, 0, 0), (1, 0, 1, 7), (2, 0, 2, 23),
            (3, 0, 3, 51), (4, 0x0002, 1, 4),
            (5, 0x0001, 0, 5), (6, 0x0004, 0, 6),
            (7, 0x0008, 0, 8), (8, 0x0200, 0, 9),
            (198, 0x8000, 2, 50), (199, 0, 3, 51),
        ]
        for idx, flags, selector, kind in rows:
            off = idx * UNIT_STRIDE
            struct.pack_into('<hh', data, off + 0xa, selector, -idx)
            data[off + 0xf] = 0x94 | (idx & 3)
            struct.pack_into('<H', data, off + 0x10, flags)
            data[off + 0x1b] = kind
        e.write(layout['units'], bytes(data))
        e.write(UNIT_ARRAY, u32(layout['units']))
        e.write(sizes, b''.join(struct.pack('<hh', i + 1, i + 2) for i in range(52)))

    t4spec.run_spec(
        SRC + 'units_update_visibility_reference.c', 'UnitsUpdateVisibility_', 0x2d650,
        cases=[
            t4spec.T4Case(mem={cheats: u32(0)}, setup=setup, label='all four fog-result combinations and each skip bit'),
            t4spec.T4Case(mem={cheats: u32(0x100)}, setup=setup, label='unrelated cheat bit'),
            t4spec.T4Case(mem={cheats: u32(0x101)}, setup=setup, label='bit zero bypasses both fog tests'),
        ],
        watch=watch, out_regs=(), init_emu=init_emu,
        stubs=[t4spec.T4Stub(0x2d5c8, log_regs=('eax', 'edx', 'ebx', 'ecx'), fn=fog)],
    )


def test_map_pick_order_target():
    watch = []
    layout = {}
    target = 0x5a7bc
    place_result = 0
    mode_result = 0

    def init_emu(e):
        layout['units'] = e.alloc(UNIT_COUNT * UNIT_STRIDE, 16)
        layout['cursor'] = e.alloc(4, 4)
        watch[:] = [(target, 4), (layout['cursor'], 4)]

    def place(e, log):
        log()
        return place_result

    def mode(e, log):
        log()
        return mode_result

    def case(label, rows=(), *, mouse=(72, 12), scroll=(0, 0), place=0, mode=1):
        def setup(e):
            nonlocal place_result, mode_result
            place_result, mode_result = place, mode
            base = layout['units']
            data = unit_records()
            for idx, x, y, flags, visibility, kind, owner in rows:
                off = idx * UNIT_STRIDE
                struct.pack_into('<HH', data, off, x & 0xffff, y & 0xffff)
                struct.pack_into('<H', data, off + 0x10, flags)
                data[off + 0xf] = visibility
                data[off + 0x1b] = kind
                data[off + 0x1e] = owner
            e.write(base, bytes(data))
            e.write(UNIT_ARRAY, u32(base))
            e.write(target, u32(unit_at(base, 100)))
            e.write(layout['cursor'], b'\x7b\xa5\x34\x12')
            e.write(0x500d0, u16(scroll[0]) + u16(scroll[1]))
            e.write(0x59428, u16(mouse[0]) + u16(mouse[1]))
            sizes = [(15, 11)] * 52
            sizes[7] = (31, 23)
            sizes[51] = (0, 0)
            e.write(0x51b9c, b''.join(struct.pack('<hh', *size) for size in sizes))

        # Resolve the cursor argument only once init_emu has allocated it.
        c = t4spec.T4Case(label=label)

        def prepare(e):
            setup(e)
            c.args = (layout['cursor'],)

        c.setup = prepare
        return c

    hit = (0, 0, 0, 0, 0, 0, 0)
    cases = [
        case('no candidate preserves cursor'),
        case('placement short-circuits mode check', [hit], place=0x8001),
        case('zero low word of mode result', [hit], mode=0x10000),
        case('owner zero wins over later overlap', [hit, (1, 0, 0, 0, 0, 0, 4)]),
        case('flag and visibility rejections before last-slot owner four', [
            (0, 0, 0, 0x0002, 0, 0, 0), (1, 0, 0, 0x0200, 0, 0, 0),
            (2, 0, 0, 0, 1, 0, 0), (199, 0, 0, 0x8000, 2, 51, 4),
        ]),
        case('inclusive hit box and nonzero non-four owner with scroll',
             [(3, 32, 48, 0, 0, 7, 2)], scroll=(2, 3), mouse=(103, 35)),
        case('one past width', [(3, 32, 48, 0, 0, 7, 2)], scroll=(2, 3), mouse=(104, 35)),
        case('one past height', [(3, 32, 48, 0, 0, 7, 2)], scroll=(2, 3), mouse=(103, 36)),
        case('negative mouse delta is outside', [hit], mouse=(71, 12)),
        case('inclusive right and bottom viewport limits',
             [(0, 240, 176, 0, 0, 0, 0)], mouse=(312, 188)),
        case('beyond right viewport limit despite mouse hit',
             [(0, 241, 176, 0, 0, 0, 0)], mouse=(313, 188)),
        case('beyond bottom viewport limit despite mouse hit',
             [(0, 240, 177, 0, 0, 0, 0)], mouse=(312, 189)),
        case('left and top edges touch viewport', [(0, -15, -11, 0, 0, 0, 0)]),
        case('box entirely left of viewport', [(0, -16, 0, 0, 0, 0, 0)], mouse=(71, 12)),
        case('box entirely above viewport', [(0, 0, -12, 0, 0, 0, 0)], mouse=(72, 11)),
        case('scroll and mouse arithmetic wraps at sixteen bits',
             [(0, 0xfff8, 0xfff4, 0, 0, 0, 4)], scroll=(0xffff, 0xffff), mouse=(80, 16)),
    ]
    t4spec.run_spec(
        SRC + 'map_pick_order_target_reference.c', 'MapPickOrderTarget_', 0x2df9c,
        cases=cases, watch=watch, out_regs=(), init_emu=init_emu,
        stubs=[t4spec.T4Stub(0x22538, log_regs=(), fn=place),
               t4spec.T4Stub(0x2b308, log_regs=(), fn=mode)],
    )


def test_simulation_tick():
    watch = []
    layout = {}
    advance_calls = {}
    current_unit = 0x50f7c
    owner_table = 0x50012
    tick_context = 0x5a7c6
    order_table = 0x5158c
    object_table = 0x511f4
    order_handlers = (0x13f60, 0x13f64)
    object_handlers = (0x11fa8, 0x11ff0, 0x12074)

    def init_emu(e):
        layout['units'] = e.alloc(UNIT_COUNT * UNIT_STRIDE, 16)
        layout['objects'] = e.alloc(OBJECT_COUNT * OBJECT_STRIDE, 16)
        watch[:] = [(layout['units'], UNIT_COUNT * UNIT_STRIDE),
                    (layout['objects'], OBJECT_COUNT * OBJECT_STRIDE),
                    (current_unit, 4), (tick_context, 2)]

    def record_gate(e, log):
        arg = e.reg('eax')
        units = layout['units']
        if units <= arg < units + UNIT_COUNT * UNIT_STRIDE:
            # Log the context at the point of use, not just its final value.
            log(arg, *e.read(tick_context, 2))
            return int(arg != unit_at(units, 4))
        log(arg)
        return int(arg != layout['objects'] + OBJECT_STRIDE + 6)

    def update_unit(e, log):
        u = e.reg('eax')
        log(u)
        if u == unit_at(layout['units'], 5):
            flags = struct.unpack('<H', e.read(u + 0x10, 2))[0]
            e.write(u + 0x10, u16(flags | 0x0800))

    def advance(e, log):
        u = e.reg('eax')
        log(u, e.reg('edx'))
        return int(u == unit_at(layout['units'], 7))

    def setup(e, active):
        units = layout['units']
        objects = layout['objects']
        data = unit_records()
        obj = bytearray(b'\x91' * (OBJECT_COUNT * OBJECT_STRIDE))
        if active:
            # index, flags, tick timer, gone timer, owner, order, tick bits
            rows = [
                (0, 0x0201, 8, 9, 0, 0, 0),
                (1, 0x0200, 8, 0, 0, 0, 0),
                (2, 0x0200, 8, 0xffff, 0, 0, 0),
                (3, 0x1000, 1, 9, 0, 0, 0),
                (4, 0, 0, 9, 1, 0, 0xff),
                (5, 0x0040, 2, 9, 2, 0, 0xdf),
                (6, 0x1840, 0, 9, 0, 0, 0),
                (7, 0, 0xffff, 9, 3, 1, 0x20),
                (8, 0, 3, 9, 0, 0, 0),
                (199, 0, 1, 9, 4, 1, 0x60),
            ]
            for idx, flags, timer, gone, owner, order, bits in rows:
                off = idx * UNIT_STRIDE
                struct.pack_into('<H', data, off + 0x10, flags)
                struct.pack_into('<H', data, off + 0x18, timer)
                data[off + 0x1e] = owner
                data[off + 0x1f] = order
                data[off + 0x49] = bits
                struct.pack_into('<H', data, off + 0x4a, gone)
            for idx, flags, kind in [(0, 0x80, 0), (1, 0, 1), (2, 0, 1), (99, 2, 2)]:
                off = idx * OBJECT_STRIDE
                obj[off + 1] = flags
                obj[off + 2] = kind
        e.write(units, bytes(data))
        e.write(objects, bytes(obj))
        e.write(UNIT_ARRAY, u32(units))
        e.write(OBJECT_ARRAY, u32(objects))
        e.write(current_unit, u32(unit_at(units, 23)))
        e.write(tick_context, b'\xdd\xee')
        e.write(owner_table, b'\x90\xa1\xb2\xc3\xfe')
        e.write(order_table, b''.join(u32(a) for a in order_handlers))
        e.write(object_table, b''.join(u32(a) for a in object_handlers))

    t4spec.run_spec(
        SRC + 'simulation_tick_reference.c', 'SimulationTick_', 0x2ec0c,
        cases=[
            t4spec.T4Case(setup=lambda e: setup(e, False), label='all slots skipped; final calls still run'),
            t4spec.T4Case(setup=lambda e: setup(e, True), label='timers, flag transitions, unit and object dispatch'),
        ],
        watch=watch, out_regs=(), init_emu=init_emu,
        stubs=[
            t4spec.T4Stub(0x10473, log_regs=('eax',), fn=record_gate),
            t4spec.T4Stub(0x2ea4c, log_regs=('eax',), fn=update_unit),
            t4spec.T4Stub(0x2edac, log_regs=('eax', 'edx'), fn=advance),
            t4spec.T4Stub(order_handlers[0], log_regs=('eax',), ret=0x10000),
            t4spec.T4Stub(order_handlers[1], log_regs=('eax',), ret=1),
            *(t4spec.T4Stub(addr, log_regs=('eax',)) for addr in object_handlers),
            t4spec.T4Stub(0x2d204, log_regs=()),
            t4spec.T4Stub(0x2d2e0, log_regs=()),
            t4spec.T4Stub(0x2ced0, log_regs=()),
        ],
    )
