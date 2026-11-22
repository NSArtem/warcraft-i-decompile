import os
import struct

import pytest
from wc1 import path, t4spec

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = 'src/mod_1e380'


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_1e380'), ['apply_scenario_terrain_kind_rects.c', 'load_scenario_placement_records.c', 'place_custom_starting_units.c'])


def test_reference_near_misses():
    t4spec.assert_ref_mismatch(path('src/mod_1e380'), ['apply_scenario_terrain_owner_rects_reference.c', 'find_custom_start_anchor_reference.c', 'load_scenario_palette_cycles_reference.c', 'load_scenario_unit_records_reference.c', 'place_custom_unit_copies_reference.c'])


def _stack_words(emu, count):
    return struct.unpack('<' + 'I' * count, emu.read(emu.reg('esp') + 4, 4 * count))


def test_apply_scenario_terrain_owner_rects():
    cases = []

    def init_emu(emu):
        records = emu.alloc(32, 16)
        owner_map = emu.alloc(256, 16)
        mapping = bytes((i + 0x80) & 0xff for i in range(256))
        for label, data in (
            ('empty', b'\xff\x42'),
            ('one record, highest map index', bytes((4, 5, 6, 7, 255, 255, 0))),
            ('two records, full-width mapped bytes', bytes((254, 255, 8, 9, 0, 0, 2, 3, 4, 127, 255, 90))),
        ):
            cases.append(t4spec.T4Case(args=(records, owner_map),
                                       mem={records: data.ljust(32, b'\0'), owner_map: mapping}, label=label))

    t4spec.run_spec(f'{SRC}/apply_scenario_terrain_owner_rects_reference.c',
                    'ApplyScenarioTerrainOwnerRects_', 0x1e3b4, cases,
                    stubs=(t4spec.T4Stub(0x2c1e8, log_regs=('eax', 'edx')),),
                    init_emu=init_emu)


def test_find_custom_start_anchor():
    cases = []

    def init_emu(emu):
        stride = 0x5c
        slots = emu.alloc(201 * stride, 16)

        def add(label, group, owner, entries, races=(1, 0)):
            data = bytearray(201 * stride)
            for i in range(201):
                struct.pack_into('<H', data, i * stride + 0x10, 0x207)
            for i, flags, slot_owner, slot_type in entries:
                base = i * stride
                struct.pack_into('<H', data, base + 0x10, flags)
                data[base + 0x1e] = slot_owner
                data[base + 0x1b] = slot_type
            cases.append(t4spec.T4Case(args=(owner,), label=label, mem={
                slots: bytes(data), 0x59640: struct.pack('<I', slots),
                0x50e52: struct.pack('<H', group), 0x50088: struct.pack('<HH', *races),
            }))

        add('group 2, player, first of two matches', 2, 0, [(0, 0x100, 0, 3), (1, 0, 0, 3)])
        add('enemy, reject each flag and mismatched owner or type', 0, 1, [
            (0, 1, 1, 40), (1, 2, 1, 40), (2, 4, 1, 40), (3, 0x200, 1, 40),
            (4, 0, 0, 40), (5, 0, 1, 41), (199, 0x8000, 1, 40),
        ])
        add('miss: only slot 200 matches', 2, 1, [(200, 0, 1, 2)])
        add('owner is not truncated to a byte', 2, 0x100, [(0, 0, 0, 2)])
        add('race-derived type is not truncated to a byte', 2, 0, [(0, 0, 0, 1)], races=(255, 0))

    t4spec.run_spec(f'{SRC}/find_custom_start_anchor_reference.c',
                    'FindCustomStartAnchor_', 0x1e3e0, cases, init_emu=init_emu)


def test_place_custom_unit_copies():
    cases = []

    def init_emu(emu):
        anchor = emu.alloc(0x5c, 16)
        data = bytearray(0x5c)
        struct.pack_into('<Hhh', data, 8, 0xcafe, -32768, 32767)

        def add(owner, count, unit_type, mask, label):
            cases.append(t4spec.T4Case(args=(owner, count & 0xffffffff, anchor, unit_type),
                                       mem={anchor: bytes(data), 0x50004: struct.pack('<I', mask)}, label=label))

        for unit_type in range(14):
            add(0, 1, unit_type, 0x80000000, f'mask only, type {unit_type}')
        add(0, 0, 10, 0x40000000, 'zero count does not set mask')
        add(0, -1, 12, 0x40000000, 'negative count sets mask but makes no copies')
        add(0, 2, 10, 0xa5000001, 'one copy and mask update')
        add(0xbeef, 4, 51, 0x24680000, 'nonplayer, three copies, last size entry')

    def place(emu, log):
        log(*(emu.reg(r) for r in ('eax', 'edx', 'ebx', 'ecx')), *_stack_words(emu, 1))
        return 0

    t4spec.run_spec(f'{SRC}/place_custom_unit_copies_reference.c',
                    'PlaceCustomUnitCopies_', 0x1e464, cases, out_regs=(),
                    watch=((0x50004, 4),), init_emu=init_emu,
                    stubs=(t4spec.T4Stub(0x2e650, log_regs=(), fn=place, stack_pop=4),))


def test_load_scenario_unit_records():
    cases = []
    watch = []
    units = []

    def init_emu(emu):
        records = emu.alloc(64, 16)
        owner_map = emu.alloc(256, 16)
        units[:] = [emu.alloc(0x5c, 16) for _ in range(2)]
        watch[:] = [(unit + 0x54, 4) for unit in units]
        mapping = bytearray(256)
        mapping[127] = 1
        mapping[255] = 0x80

        def add(label, stream, custom, race, enemy):
            cases.append(t4spec.T4Case(args=(records, owner_map), label=label, mem={
                records: bytes(stream).ljust(64, b'\0'), owner_map: bytes(mapping),
                0x50e4e: struct.pack('<H', custom), 0x50088: struct.pack('<HH', race, enemy),
                0x51122: bytes(i ^ 1 for i in range(12)),
                units[0]: struct.pack('<I', 0xf1234567).rjust(0x58, b'\0') + b'\0' * 4,
                units[1]: struct.pack('<I', 999).rjust(0x58, b'\0') + b'\0' * 4,
            }))

        add('empty', (255, 0), 1, 1, 1)
        add('noncustom, owner remap but no race swap', (1, 255, 4, 127, 255, 0), 0, 1, 1)
        add('swap player and enemy types; do not swap other owner',
            (1, 254, 0, 0, 254, 255, 2, 0, 11, 127, 3, 4, 50, 255, 255, 0), 1, 1, 1)
        add('race values other than one leave types unchanged',
            (1, 2, 7, 0, 2, 3, 9, 127, 255, 0), 2, 2, 0)
        add('null creation consumes amount suffix; next unit still loads',
            (0, 5, 50, 0, 254, 13, 1, 6, 3, 127, 255, 0), 0, 0, 0)
        add('type 50 rounds an existing unsigned amount and an explicit amount',
            (1, 2, 50, 0, 2, 3, 50, 127, 254, 255, 255, 0), 0, 0, 0)

    def create(emu, log):
        x, y, unit_type, owner = (emu.reg(r) for r in ('eax', 'edx', 'ebx', 'ecx'))
        log(x, y, unit_type, owner)
        if x == 0:
            return 0
        return units[((x >> 3) - 1) & 1]

    t4spec.run_spec(f'{SRC}/load_scenario_unit_records_reference.c',
                    'LoadScenarioUnitRecords_', 0x1e644, cases, watch=watch,
                    stubs=(t4spec.T4Stub(0x2e6f4, log_regs=(), fn=create),), init_emu=init_emu)


def test_load_scenario_palette_cycles():
    cases = []

    def init_emu(emu):
        records = emu.alloc(96, 16)
        full = bytes(v for i in range(17) for v in (i + 1, i, 255 - i))
        for label, mask, data in (
            ('empty: clear only', 0xffff, b'\0'),
            ('one disabled cycle', 0, bytes((255, 0, 255, 0))),
            ('selective enables', 0b101, bytes((1, 0, 255, 128, 250, 3, 254, 10, 20, 0))),
            ('bit 15 enables ID 15 but not ID 16', 0x8000, full + b'\0'),
        ):
            cases.append(t4spec.T4Case(args=(records,), label=label, mem={
                records: data.ljust(96, b'\xff'), 0x500de: struct.pack('<H', mask),
            }))

    def stack_logger(count):
        def stub(emu, log):
            log(*_stack_words(emu, count))
            return 0
        return stub

    t4spec.run_spec(f'{SRC}/load_scenario_palette_cycles_reference.c',
                    'LoadScenarioPaletteCycles_', 0x1e724, cases, init_emu=init_emu,
                    stubs=(t4spec.T4Stub(0x334fc, log_regs=()),
                           t4spec.T4Stub(0x34860, log_regs=(), fn=stack_logger(6)),
                           t4spec.T4Stub(0x31920, log_regs=(), fn=stack_logger(1))))
