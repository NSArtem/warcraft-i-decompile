import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = 'src/mod_1c9c0'
GRAPHICS_MAP = 0x5180e
RESOURCE_TABLE = 0x52214
COMMON = 0x522a8
SIDE = 0x522d8


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_1c9c0'), ['is_graphics_resource_allowed_for_scenario.c'])


def test_reference_mismatches():
    t4spec.assert_ref_mismatch(path('src/mod_1c9c0'), ['clone_sprite_resource_reference.c', 'free_session_graphics_reference.c', 'load_session_graphics_reference.c', 'unit_update_graphics_index_reference.c'])


def test_unit_update_graphics_index():
    # (type, flags at +0x10, flags at +0x49, selector at +0x1e, mapped index)
    inputs = [
        (0, 0, 0, 0, 0xff),
        (1, 0x8000, 0, 4, 0x80),
        (4, 0x0080, 0, 0, 0xa7),
        (0xff, 0x0080, 0, 0xff, 0x17),
        (0x33, 0, 0, 0, 0x26),
        (0x15, 0, 0, 0, 0x27),
        (0x18, 0, 0, 0, 0x28),
        (0x0f, 0, 0, 4, 0x29),
        (0x32, 0, 0, 4, 0x2a),
        (0x33, 0, 0, 4, 0x2b),
        (0x15, 0, 0, 4, 0x2c),
        (0x0f, 0, 0, 1, 0x2d),
    ]
    inputs += [(kind, 0, bits, selector, 0xe9)
               for kind in (2, 3) for bits in (0, 0x20, 0x80, 0xa0)
               for selector in (0, 4, 0x80)]
    cases = []
    watch = []

    def init_emu(emu):
        unit = emu.alloc(0x50, 16)
        watch[:] = [(unit, 0x50)]
        for kind, flags, bits, selector, mapped in inputs:
            image = bytearray(b'\xa5' * 0x50)
            struct.pack_into('<H', image, 0x10, flags)
            image[0x1b] = kind
            image[0x1e] = selector
            image[0x49] = bits
            cases.append(T4Case(
                args=(unit,),
                mem={unit: bytes(image), GRAPHICS_MAP + 2 * kind: bytes((mapped, 0x6b))},
                label=f'type={kind:#x}, flags={flags:#x}/{bits:#x}, selector={selector:#x}',
            ))

    t4spec.run_spec(f'{SRC}/unit_update_graphics_index_reference.c',
                    'UnitUpdateGraphicsIndex_', 0x1c9c0, cases,
                    watch=watch, out_regs=(), init_emu=init_emu)


def test_clone_sprite_resource():
    capacity = 512
    cases = []
    watch = []
    stubs = []

    def copy_pixels(emu, log):
        dest, src, count = (emu.reg(r) for r in ('eax', 'edx', 'ebx'))
        log(dest, src, count)
        if count:
            emu.write(dest, emu.read(src, count))

    def init_emu(emu):
        src = emu.alloc(capacity, 16)
        dest = emu.alloc(capacity, 16)
        watch[:] = [(dest, capacity), (src, capacity)]
        stubs[:] = [T4Stub(0x32558, ret=dest, log_regs=('eax',)),
                    T4Stub(0x103ba, log_regs=('eax', 'edx', 'ebx'), fn=copy_pixels)]
        for label, size, entries in (
            ('zero-count-still-copies-prefix', 12, ()),
            ('one-frame', 128, ((3, 5, 96),)),
            ('zero-width-and-zero-height', 128, ((0, 7, 80), (6, 0, 112))),
            ('multiple-frames-nonmonotonic-offsets', 384,
             ((7, 9, 288), (255, 1, 32), (2, 3, 360))),
        ):
            image = bytearray((i * 37 + 11) & 0xff for i in range(capacity))
            struct.pack_into('<HH', image, 0, len(entries), 0xb17e)
            for i, (width, height, offset) in enumerate(entries):
                struct.pack_into('<HBBI', image, 4 + 8 * i, 0xab00 + i,
                                 width, height, offset)
            cases.append(T4Case(args=(src, size), label=label,
                                mem={src: bytes(image), dest: b'\xcd' * capacity}))

    t4spec.run_spec(f'{SRC}/clone_sprite_resource_reference.c',
                    'CloneSpriteResource_', 0x1ca84, cases,
                    watch=watch, stubs=stubs, out_regs=('eax',), init_emu=init_emu)


def test_load_session_graphics():
    def allowed(emu, log):
        resource_id = emu.reg('eax')
        log(resource_id)
        return int(resource_id != 0x127)

    def make_case(label, player, enemy, descriptors):
        assert len(descriptors) == 72
        return T4Case(label=label, mem={
            0x50088: struct.pack('<HH', player, enemy),
            RESOURCE_TABLE: struct.pack('<74H', 0x4000, 0x8000, *descriptors),
            COMMON: struct.pack('<12I', *(0x10000 + i * 4 for i in range(12))),
            SIDE: struct.pack('<144I', *(0x20000 + i * 4 for i in range(144))),
        })

    descriptors = [0x0123, 0x4124, 0x8125, 0xc126, 0xd127,
                   0xd128, 0x2129, 0x612a, 0x912b] + [0] * 62 + [0xc12c]
    cases = [
        make_case('empty-side-table', 0, 1, [0] * 72),
        make_case('mixed-masks-and-filter-results', 0, 1, descriptors),
        make_case('reversed-races', 1, 0, descriptors),
        make_case('same-race', 0, 0, descriptors),
        make_case('all-shared', 0, 1, [0xc200 + i for i in range(72)]),
    ]
    t4spec.run_spec(f'{SRC}/load_session_graphics_reference.c',
                    'LoadSessionGraphics_', 0x1cb90, cases, out_regs=(),
                    watch=[(COMMON, 12 * 4), (SIDE, 144 * 4)], log_cap=4096,
                    stubs=[T4Stub(0x31870, ret=0x178, log_regs=('eax', 'edx')),
                           T4Stub(0x32740, ret=0x36000, log_regs=('eax', 'edx')),
                           T4Stub(0x1cb04, log_regs=('eax',), fn=allowed),
                           T4Stub(0x1ca84, ret=0x37000, log_regs=('eax', 'edx'))])


def test_free_session_graphics():
    def make_case(label, side_indices, common_indices):
        side = [0] * 144
        common = [0] * 12
        for i in side_indices:
            side[i] = 0x36000 + i * 16
        for i in common_indices:
            common[i] = 0x38000 + i * 16
        return T4Case(label=label, mem={
            SIDE: struct.pack('<144I', *side),
            COMMON: struct.pack('<12I', *common),
            SIDE + 144 * 4: struct.pack('<I', 0x3a000),
        })

    cases = [make_case('empty', (), ()),
             make_case('sparse-including-endpoints', (0, 1, 71, 142, 143), (0, 5, 11)),
             make_case('fully-populated', range(144), range(12))]
    t4spec.run_spec(f'{SRC}/free_session_graphics_reference.c',
                    'FreeSessionGraphics_', 0x1ccdc, cases, out_regs=(),
                    watch=[(SIDE, 145 * 4), (COMMON, 12 * 4)], log_cap=2048,
                    stubs=[T4Stub(0x32780, log_regs=('eax',))])
