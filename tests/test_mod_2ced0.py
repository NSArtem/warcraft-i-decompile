import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = 'src/mod_2ced0'


def test_reference_near_misses():
    t4spec.assert_ref_mismatch(path('src/mod_2ced0'), ['find_nearby_clear_tile_reference.c', 'fog_rect_matches_mask_reference.c', 'update_unit_timers_and_resources_reference.c'])


def test_update_unit_timers_and_resources():
    stride = 0x5c
    units = bytearray(200 * stride)
    for i in range(200):
        struct.pack_into('<H', units, i * stride + 0x10, 0x200)

    def slot(i, kind, *, flags=0, resource=0, period=1, player=0,
             health=0, timer36=3, timer38=0xffff):
        off = i * stride
        struct.pack_into('<H', units, off + 0x10, flags)
        struct.pack_into('<H', units, off + 0x16, health)
        units[off + 0x1a] = resource
        units[off + 0x1b] = kind
        units[off + 0x1e] = player
        struct.pack_into('<HH', units, off + 0x36, timer36, timer38)
        units[off + 0x48] = period

    slot(0, 10, resource=254, player=4)
    slot(1, 14, resource=1, flags=0x400)
    slot(2, 12, resource=255)
    slot(3, 13, resource=1, period=0)
    slot(4, 11, resource=1, period=2)
    slot(5, 9, resource=2)
    slot(6, 15, health=5, timer36=0, timer38=0)
    slot(7, 15, health=4)
    slot(8, 9, flags=0x400, resource=2)
    slot(9, 8, resource=2)
    slot(10, 9, flags=1, resource=2)
    slot(11, 9, flags=2, resource=2)
    slot(12, 9, flags=4, resource=2)
    slot(13, 9, period=0, resource=2)
    slot(14, 15, health=0x8000)
    slot(199, 15, resource=1, timer36=0x8000, timer38=1)
    decay = bytearray(256)
    decay[9], decay[15], decay[16] = 7, 11, 23

    watch = []
    cases = []
    random_returns = {}

    def init_emu(emu):
        base = emu.alloc(len(units), 16)
        watch[:] = [(base, len(units)), (0x55281, 5)]
        for label, returns, dx, dy in (
            ('drift-gate-closed', {5: 0x10f}, -8, 9),
            ('x-signed-remainder-lower-clamp', {5: 0x10, 6: 3, 7: -2}, -2, 9),
            ('y-upper-clamp', {5: 0, 6: 2, 8: 2}, -9, 2),
            ('x-in-range', {5: 0, 6: 1, 7: 5}, 0, -1),
            ('y-in-range', {5: 0, 6: 0, 8: 0}, 1, 0),
        ):
            def setup(e, values=returns):
                random_returns.clear()
                random_returns.update(values)

            cases.append(t4spec.T4Case(label=label, setup=setup, mem={
                base: bytes(units),
                0x59640: struct.pack('<I', base),
                0x55281: struct.pack('<3B2b', 0x81, 0x52, 0x39, dx, dy),
                0x5008c: bytes((2, 0, 0, 0, 1)),
                0x51df0: bytes(decay),
            }))

    def random_value(e, log):
        arg = e.reg('eax')
        log(arg)
        return random_returns.get(arg, 0) & 0xffffffff

    def remove(e, log):
        unit = e.reg('eax')
        log(unit)
        # Make reloading the type after UnitRemove observable.
        e.write(unit + 0x1b, b'\x10')
        return 0

    t4spec.run_spec(f'{SRC}/update_unit_timers_and_resources_reference.c',
                    'UpdateUnitTimersAndResources_', 0x2d2e0, cases,
                    init_emu=init_emu, watch=watch, out_regs=(), stubs=(
                        t4spec.T4Stub(0x19478, log_regs=('eax',), fn=random_value),
                        t4spec.T4Stub(0x2e14c, log_regs=('eax',), fn=remove),
                    ))


def test_fog_rect_matches_mask():
    watch = []
    cases = []

    def init_emu(emu):
        fog = emu.alloc(64 * 64 * 2, 16)
        xy = emu.alloc(4, 4)
        size = emu.alloc(4, 4)
        watch[:] = [(xy, 4), (size, 4)]

        def case(label, x, y, w, h, mask, wanted, cells=()):
            tiles = bytearray(64 * 64 * 2)
            for index, value in cells:
                struct.pack_into('<H', tiles, index * 2, value)
            cases.append(t4spec.T4Case(
                args=(xy, size, mask, wanted), label=label, mem={
                    0x58578: struct.pack('<I', fog), fog: bytes(tiles),
                    xy: struct.pack('<hh', x, y), size: struct.pack('<hh', w, h),
                }))

        first = 4 * 64 + 3
        matching = [(first, 0x8001), (first + 1, 0x8021),
                    (first + 64, 0x8041), (first + 65, 0x8081)]
        case('two-rows-ignore-unmasked-bits', 3, 4, 2, 2, 0x8001, 0x8001, matching)
        case('first-cell-mismatch', 3, 4, 2, 2, 0x8001, 0x8001, matching[1:])
        case('last-cell-second-row-mismatch', 3, 4, 2, 2, 0x8001, 0x8001, matching[:-1])
        case('zero-width', 3, 4, 0, 3, 0xffff, 1)
        case('zero-height', 3, 4, 3, 0, 0xffff, 1)
        case('expected-is-not-masked', 3, 4, 1, 1, 0, 1, matching)
        case('signed-x-stays-in-buffer', -1, 1, 2, 1, 0xffff, 7, [(63, 7), (64, 7)])
        case('last-map-cell', 63, 63, 1, 1, 0xffff, 0xffff, [(4095, 0xffff)])

    t4spec.run_spec(f'{SRC}/fog_rect_matches_mask_reference.c',
                    'FogRectMatchesMask_', 0x2d5c8, cases,
                    init_emu=init_emu, watch=watch, out_regs=('eax',))


def _pack_pair(lo, hi):
    return (lo & 0xffff) | ((hi & 0xffff) << 16)


def test_find_nearby_clear_tile():
    watch = []
    cases = []
    clear = None

    def init_emu(emu):
        xp = emu.alloc(2, 2)
        yp = emu.alloc(2, 2)
        watch[:] = [(xp, 2), (yp, 2)]
        tables = {
            0x5515c: struct.pack('<4h', 1, 0, -1, 0),
            0x55164: struct.pack('<4h', 0, 1, 0, -1),
            0x552b8: struct.pack('<4h', 1, -1, -1, 1),
            0x552c0: struct.pack('<4h', 1, -1, 1, 1),
            0x552c8: struct.pack('<4H', 0, 1, 3, 2),
        }

        def case(label, x, y, w, h, tx, ty, clear_tile):
            def setup(e):
                nonlocal clear
                clear = clear_tile

            mem = dict(tables)
            mem[xp] = struct.pack('<h', x)
            mem[yp] = struct.pack('<h', y)
            cases.append(t4spec.T4Case(
                args=(xp, yp, _pack_pair(w, h), _pack_pair(tx, ty)),
                label=label, setup=setup, mem=mem))

        case('top-left-equality', 20, 20, 2, 3, 20, 20, (19, 19))
        case('top-right', 20, 20, 2, 3, 21, 20, (22, 19))
        case('bottom-left', 20, 20, 2, 3, 20, 21, (19, 23))
        case('bottom-right', 20, 20, 2, 3, 21, 21, (22, 23))
        case('blocked-first-edge-turns-corner', 20, 20, 2, 3, 20, 20, (22, 20))
        case('first-ring-blocked-expand', 20, 20, 2, 3, 20, 20, (18, 18))
        case('skip-negative-coordinates', 0, 0, 2, 2, -1, -1, (2, 0))
        case('skip-coordinates-at-or-above-64', 62, 62, 3, 3, 63, 63, (63, 61))
        case('width-guard-keeps-coordinates', 20, 20, 12, 3, 21, 21, None)
        case('width-just-below-guard', 20, 20, 11, 3, 21, 21, (31, 23))

    def tile_in_use(e, log):
        x = e.reg('eax')
        y = e.reg('edx')
        log(x, y, e.reg('ebx'))
        # Only AX is meaningful to the caller.
        return 0x10000 if (x, y) == clear else 1

    t4spec.run_spec(f'{SRC}/find_nearby_clear_tile_reference.c',
                    'FindNearbyClearTile_', 0x2e464, cases,
                    init_emu=init_emu, watch=watch, out_regs=('eax',), stubs=(
                        t4spec.T4Stub(0x13348, log_regs=('eax', 'edx', 'ebx'), fn=tile_in_use),
                    ))
