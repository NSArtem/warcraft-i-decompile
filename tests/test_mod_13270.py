import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = 'src/mod_13270'
UNIT_TYPE_SIZE = 0x51ABC
CLASS_MASKS = 0x51DD4
MAP_FLAGS = 0x5857C
OBJECT_MAP = 0x58580
SIDE = 64
CELLS = SIDE * SIDE
UNIT_SIZE = 0x20


def test_reference_near_misses():
    t4spec.assert_ref_mismatch(path('src/mod_13270'), ['can_place_unit_footprint_reference.c', 'clear_unit_footprint_reference.c', 'has_join_candidate_nearby_reference.c', 'mark_unit_footprint_reference.c'])


def _unit(x=0, y=0, *, flags=0, type_id=0, map_class=0):
    data = bytearray(UNIT_SIZE)
    struct.pack_into('<hh', data, 0x0A, x, y)
    struct.pack_into('<H', data, 0x10, flags)
    data[0x1B] = type_id
    data[0x1E] = map_class
    return bytes(data)


def _size(type_id, width, height):
    return {UNIT_TYPE_SIZE + 4 * type_id: struct.pack('<HH', width, height)}


class _Board:
    def __init__(self):
        self.watch = []
        self.unit_cases = []

    def init_emu(self, emu):
        self.flags = emu.alloc(CELLS * 2, 16)
        self.objects = emu.alloc(CELLS * 4, 16)
        self.unit = emu.alloc(UNIT_SIZE, 16)
        self.candidates = emu.alloc(9 * UNIT_SIZE, 16)
        self.watch[:] = [(self.flags, CELLS * 2), (self.objects, CELLS * 4),
                         (MAP_FLAGS, 8)]
        for case in self.unit_cases:
            case.args = (self.unit,)

    def case(self, label, *, args=(), unit=None, mem=None,
             dirty=False, tiles=(), occupants=()):
        def setup(emu):
            emu.write(MAP_FLAGS, struct.pack('<II', self.flags, self.objects))
            if dirty:
                # Alternate set and clear occupancy bits; keep unrelated bits.
                flags_image = struct.pack('<HH', 0xA421, 0xFFFF) * (CELLS // 2)
                objects_image = struct.pack('<I', self.candidates) * CELLS
            else:
                flags_image = bytes(CELLS * 2)
                objects_image = bytes(CELLS * 4)
            emu.write(self.flags, flags_image)
            emu.write(self.objects, objects_image)
            if unit is not None:
                emu.write(self.unit, unit)
            for x, y, flags in tiles:
                emu.write(self.flags + 2 * (y * SIDE + x), struct.pack('<H', flags))
            for i, (x, y, flags, map_class) in enumerate(occupants):
                candidate = self.candidates + i * UNIT_SIZE
                emu.write(candidate, _unit(x, y, flags=flags, map_class=map_class))
                emu.write(self.objects + 4 * (y * SIDE + x), struct.pack('<I', candidate))

        case = t4spec.T4Case(label=label, args=args, mem=mem or {}, setup=setup)
        if unit is not None:
            self.unit_cases.append(case)
        return case


def _footprint_cases(board):
    cases = []
    for label, x, y, width, height, type_id, map_class, mask in (
        ('single tile, zero class mask', 9, 11, 1, 1, 0, 0, 0),
        ('non-square footprint with row gaps', 7, 12, 3, 2, 31, 1, 0x8401),
        ('bottom and right edges', 62, 61, 2, 3, 51, 2, 0x0020),
        ('two full rows, no row gap', 0, 62, 64, 2, 32, 3, 0x0040),
        ('zero width', 8, 4, 0, 3, 3, 2, 0x0020),
        ('zero height', 8, 4, 3, 0, 4, 1, 0x8401),
    ):
        mem = _size(type_id, width, height)
        mem[CLASS_MASKS + 2 * map_class] = struct.pack('<H', mask)
        cases.append(board.case(label, unit=_unit(x, y, type_id=type_id, map_class=map_class),
                                mem=mem, dirty=True))
    return cases


def test_mark_unit_footprint():
    board = _Board()
    t4spec.run_spec(f'{SRC}/mark_unit_footprint_reference.c', 'MarkUnitFootprint_',
                    0x1379C, _footprint_cases(board), init_emu=board.init_emu,
                    watch=board.watch, out_regs=())


def test_clear_unit_footprint():
    board = _Board()
    t4spec.run_spec(f'{SRC}/clear_unit_footprint_reference.c', 'ClearUnitFootprint_',
                    0x13860, _footprint_cases(board), init_emu=board.init_emu,
                    watch=board.watch, out_regs=())


def test_can_place_unit_footprint():
    board = _Board()

    def case(label, x, y, width=3, height=2, type_id=31, tiles=()):
        return board.case(label, args=(x & 0xFFFF, y & 0xFFFF, type_id),
                          mem=_size(type_id, width, height), tiles=tiles)

    cases = [
        case('empty rectangle', 10, 20),
        case('negative x', -1, 20),
        case('negative y', 10, -1),
        case('crosses right edge', 62, 20),
        case('crosses bottom edge', 10, 63),
        case('touches both edges', 61, 62),
        case('common blocker in first tile', 10, 20, tiles=((10, 20, 0x0200),)),
        case('common blocker in last tile', 61, 62, tiles=((63, 63, 0x0004),)),
        case('row gap and adjacent row ignored', 10, 20,
             tiles=((13, 20, 0xFFFF), (9, 21, 0xFFFF), (10, 22, 0xFFFF))),
        case('unrelated high bits ignored', 10, 20, tiles=((12, 21, 0x8000),)),
        case('type 31 ignores bit 0x10', 10, 20, tiles=((12, 21, 0x0010),)),
        case('type 32 blocks bit 0x10', 10, 20, type_id=32, tiles=((12, 21, 0x0010),)),
        case('zero width at x=64', 64, 20, width=0, tiles=((0, 21, 0xFFFF),)),
        case('zero height at y=64', 10, 64, height=0),
        case('zero width still checks x bound', 65, 20, width=0),
        case('zero height still checks y bound', 10, 65, height=0),
        case('width is unsigned', 0, 0, width=0xFFFF),
        case('height is unsigned', 0, 0, height=0xFFFF),
    ]
    t4spec.run_spec(f'{SRC}/can_place_unit_footprint_reference.c',
                    'CanPlaceUnitFootprint_', 0x13990, cases,
                    init_emu=board.init_emu, watch=board.watch, out_regs=('eax',))


def test_has_join_candidate_nearby():
    board = _Board()

    def case(label, x, y, *occupants):
        return board.case(label, unit=_unit(x, y), occupants=occupants)

    cases = [
        case('empty neighborhood', 25, 30),
        case('first slot qualifies', 25, 30, (24, 29, 0, 0)),
        case('center qualifies', 25, 30, (25, 30, 0, 0)),
        case('last slot qualifies after rejections', 25, 30,
             (24, 29, 0, 1), (25, 30, 0x0200, 0), (26, 31, 0x8008, 0)),
        case('nonzero class rejects', 25, 30, (25, 30, 0, 1)),
        case('candidate outside the 3x3 window', 25, 30, (27, 30, 0, 0)),
        case('top-left clipped, in-bounds match', 0, 0, (1, 1, 0, 0)),
        case('bottom-right clipped, in-bounds match', 63, 63, (63, 63, 0, 0)),
        case('left edge must not wrap to prior row', 0, 20, (63, 18, 0, 0)),
        case('right edge must not wrap to next row', 63, 20, (0, 21, 0, 0)),
    ]
    for bit in (0x0001, 0x0002, 0x0004, 0x0200):
        cases.append(case(f'flag {bit:#06x} rejects', 25, 30, (25, 30, bit, 0)))
    t4spec.run_spec(f'{SRC}/has_join_candidate_nearby_reference.c',
                    'HasJoinCandidateNearby_', 0x13A90, cases,
                    init_emu=board.init_emu, watch=board.watch, out_regs=('eax',))
