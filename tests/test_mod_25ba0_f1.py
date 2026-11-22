import os
import struct

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = 'src/mod_25ba0'
RACE = 0x50088
CREATURE = 0x51cc0
MASKS = 0x51dbc
UNIT_ARRAY = 0x59640
SLOTS = 0x5a0f0
COUNTS = 0x5a110
USE_TYPE = 0x5a116
LOCAL = 0x5a118
PLAYER = 0x5a11a
FIRST_TYPE = 0x5a11c
STRIDE = 0x5c


def words(*values):
    return struct.pack('<' + 'H' * len(values), *values)


def pointers(*values):
    return struct.pack('<' + 'I' * len(values), *values)


def unit(flags=0, base=3, display=17, owner=0):
    record = bytearray(STRIDE)
    struct.pack_into('<H', record, 0x10, flags)
    record[0x1b] = base
    record[0x1c] = display
    record[0x1e] = owner
    return bytes(record)


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_25ba0'), ['selection_restore_display_types.c', 'selection_set_display_type.c'])


def test_reference_near_misses():
    t4spec.assert_ref_mismatch(path('src/mod_25ba0'), ['selection_clear_current_reference.c', 'selection_rebuild_from_unit_flags_reference.c', 'selection_refresh_status_reference.c', 'selection_remove_unit_reference.c'])


def test_selection_rebuild_from_unit_flags():
    cases = []
    watch = []

    def init_emu(emu):
        base = emu.alloc(200 * STRIDE, 16)
        watch[:] = [(SLOTS, 32), (COUNTS, 4), (LOCAL, 4), (base, 200 * STRIDE)]
        for label, hits, initial_player in (
            ('no selected units', {}, 1),
            ('first and last records; shared and unrelated bits',
             {0: 0x2040, 1: 0x0004, 121: 0x0044, 199: 0x2000}, 0),
            ('four matches per player',
             {4: 0x0040, 7: 0x2040, 9: 0x2040, 13: 0x2000,
              100: 0x0040, 198: 0x2000}, 1),
        ):
            image = b''.join(unit(flags=hits.get(i, 0)) for i in range(200))
            cases.append(t4spec.T4Case(label=label, mem={
                UNIT_ARRAY: pointers(base), MASKS: words(0x0040, 0x2000),
                SLOTS: pointers(*([base] * 8)), COUNTS: words(3, 4),
                LOCAL: words(0, initial_player), base: image,
            }))

    def memset(emu, log):
        dst, value, size = (emu.reg(reg) for reg in ('eax', 'edx', 'ebx'))
        log(dst, value, size)
        emu.write(dst, bytes([value & 0xff]) * size)
        return dst

    def apply_selection(emu, log):
        count = emu.reg('eax') & 0xffff
        array = emu.reg('edx')
        assert count <= 4
        player = struct.unpack('<H', emu.read(PLAYER, 2))[0]
        assert player < 2
        payload = emu.read(array, count * 4) if count else b''
        # Compare pointees, not the address of the caller's stack array.
        log(count, player, *struct.unpack('<' + 'I' * count, payload))
        emu.write(SLOTS + 16 * player, payload.ljust(16, b'\x00'))
        emu.write(COUNTS + 2 * player, words(count))

    t4spec.run_spec(
        SRC + '/selection_rebuild_from_unit_flags_reference.c',
        'SelectionRebuildFromUnitFlags_', 0x25ba0, cases,
        watch=watch, out_regs=(), init_emu=init_emu,
        stubs=(t4spec.T4Stub(0x30c50, log_regs=('eax', 'edx', 'ebx'), fn=memset),
               t4spec.T4Stub(0x25f9c, log_regs=('eax',), fn=apply_selection)),
    )


def test_selection_clear_current():
    cases = []
    watch = []

    def init_emu(emu):
        a = emu.alloc(3 * STRIDE, 16)
        b, c = a + STRIDE, a + 2 * STRIDE
        watch[:] = [(SLOTS, 32), (COUNTS, 4), (LOCAL, 4), (a, 3 * STRIDE)]
        for label, player, slots, counts in (
            ('local sparse row', 0, (a, 0, 0, b, 0, c, 0, 0), (2, 1)),
            ('remote sparse row', 1, (c, 0, 0, 0, 0, a, 0, b), (1, 2)),
            ('empty local row', 0, (0, 0, 0, 0, c, 0, 0, 0), (0, 1)),
        ):
            cases.append(t4spec.T4Case(label=label, mem={
                MASKS: words(0x0040, 0x2000), SLOTS: pointers(*slots),
                COUNTS: words(*counts), LOCAL: words(0, player),
                a: unit(0x2044, 3, 19) + unit(0x2048, 4, 20) + unit(0x2040, 5, 21),
            }))

    t4spec.run_spec(
        SRC + '/selection_clear_current_reference.c', 'SelectionClearCurrent_',
        0x25cd8, cases, watch=watch, out_regs=(), init_emu=init_emu,
        stubs=(t4spec.T4Stub(0x290f8, log_regs=('eax',)),),
    )


def test_selection_refresh_status():
    cases = []
    watch = []
    state = {}

    def init_emu(emu):
        # At 0x25e1d the original XORs DH with AH from the returned pointer.
        # Keep AH zero on these iterator fixtures to exercise the boolean path.
        raw = emu.alloc(0x10000 + 3 * STRIDE, 16)
        a = (raw + 0xffff) & ~0xffff
        b, c = a + STRIDE, a + 2 * STRIDE
        cursor = emu.alloc(20, 16)
        state['cursor'] = cursor
        watch[:] = [(USE_TYPE, 4), (FIRST_TYPE, 1), (a, 3 * STRIDE)]
        for label, race, first, display, tail, second, third, owner, creature in (
            ('empty selection preserves status', 0, 0, 17, (0, 0, 0), 17, 17, 0, 1),
            ('single local creature', 0, a, 17, (0, 0, 0), 17, 17, 0, 1),
            ('matching displays; remote owner', 0, a, 17, (b, c, 0), 17, 17, 1, 1),
            ('mixed displays; non-creature', 1, a, 17, (b, c, 0), 18, 17, 0, 0),
            ('first display already equals race default', 1, a, 0x3c, (b, c, 0), 18, 17, 0, 1),
        ):
            cases.append(t4spec.T4Case(label=label, mem={
                cursor: pointers(0, first, *tail), RACE: words(race),
                CREATURE: words(0, 0, 0, creature), USE_TYPE: words(7, 9),
                FIRST_TYPE: b'\xee',
                a: unit(base=3, display=display, owner=owner)
                + unit(display=second) + unit(display=third),
            }))

    def first(emu, log):
        log()
        cursor = state['cursor']
        emu.write(cursor, pointers(0))
        return struct.unpack('<I', emu.read(cursor + 4, 4))[0]

    def next_unit(emu, log):
        log()
        cursor = state['cursor']
        i = struct.unpack('<I', emu.read(cursor, 4))[0]
        assert i < 3
        emu.write(cursor, pointers(i + 1))
        return struct.unpack('<I', emu.read(cursor + 8 + 4 * i, 4))[0]

    def set_type(emu, log):
        log(emu.reg('eax') & 0xffff)

    t4spec.run_spec(
        SRC + '/selection_refresh_status_reference.c', 'SelectionRefreshStatus_',
        0x25d98, cases, watch=watch, out_regs=(), init_emu=init_emu,
        stubs=(t4spec.T4Stub(0x25cc4, log_regs=(), fn=first),
               t4spec.T4Stub(0x25c50, log_regs=(), fn=next_unit),
               t4spec.T4Stub(0x25d60, log_regs=('eax',), fn=set_type),
               t4spec.T4Stub(0x290f8, log_regs=('eax',))),
    )


def test_selection_remove_unit():
    cases = []
    watch = []
    state = {}

    def init_emu(emu):
        a = emu.alloc(2 * STRIDE, 16)
        b = a + STRIDE
        control = emu.alloc(8, 16)
        state.update(control=control, survivor=b)
        watch[:] = [(SLOTS, 32), (COUNTS, 4), (USE_TYPE, 6), (a, 2 * STRIDE)]
        for label, flags, slots, counts, use_type, active, dialog in (
            ('unselected unit leaves both rows alone', 0x0004,
             (b, 0, 0, 0, b, 0, 0, 0), (1, 1), 1, 1, 1),
            ('last local and remote selection; cancel active modes', 0x2044,
             (a, 0, 0, 0, 0, 0, 0, a), (1, 1), 1, 1, 1),
            ('remote only; zero low word from mode predicate', 0x2008,
             (b, 0, 0, 0, 0, a, 0, 0), (1, 1), 1, 0, 0x10000),
            ('one local survivor uses its display type', 0x0044,
             (a, 0, b, 0, 0, 0, 0, 0), (2, 0), 1, 0, 0),
            ('one local survivor refreshes shared display type', 0x0044,
             (a, b, 0, 0, 0, 0, 0, 0), (2, 0), 0, 0, 0),
            ('multiple local survivors; all matching slots cleared', 0x0044,
             (a, b, a, b, 0, 0, 0, 0), (4, 0), 1, 0, 0),
        ):
            cases.append(t4spec.T4Case(label=label, args=(a,), mem={
                MASKS: words(0x0040, 0x2000), SLOTS: pointers(*slots),
                COUNTS: words(*counts), USE_TYPE: words(use_type, 0, 1),
                a: unit(flags, 3, 19) + unit(0x0040, 4, 20),
                control: pointers(active, dialog),
            }))

    def predicate(offset):
        def stub(emu, log):
            log()
            return struct.unpack('<I', emu.read(state['control'] + offset, 4))[0]
        return stub

    def first(emu, log):
        log()
        return state['survivor']

    t4spec.run_spec(
        SRC + '/selection_remove_unit_reference.c', 'SelectionRemoveUnit_',
        0x25e58, cases, watch=watch, out_regs=(), init_emu=init_emu,
        stubs=(t4spec.T4Stub(0x22538, log_regs=(), fn=predicate(0)),
               t4spec.T4Stub(0x22930, log_regs=()),
               t4spec.T4Stub(0x2b308, log_regs=(), fn=predicate(4)),
               t4spec.T4Stub(0x2b390, log_regs=()),
               t4spec.T4Stub(0x25d7c, log_regs=()),
               t4spec.T4Stub(0x25d98, log_regs=()),
               t4spec.T4Stub(0x25cc4, log_regs=(), fn=first),
               t4spec.T4Stub(0x290f8, log_regs=('eax',))),
    )
