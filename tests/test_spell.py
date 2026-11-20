import os

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')

SRC = path('src', 'spell')

U = 0x300000      # unit under test
T = 0x300400      # target unit
ARR = 0x301000    # unit array
HP_TAB = 0x302000

ARENA = 0x300000
ARENA_SIZE = 0x10000


def f(name):
    return os.path.join(SRC, name)


def mk(fields):
    b = bytearray(0x5c)
    for off, (sz, v) in fields.items():
        b[off:off + sz] = int(v).to_bytes(sz, 'little')
    return bytes(b)


def map_arena(e):
    """Map the scratch region used for the synthetic unit structs."""
    try:
        e.uc.mem_map(ARENA, ARENA_SIZE)
    except Exception:
        pass


def test_t3_matches():
    t4spec.assert_t3_matches(path('src', 'spell'), [
        'spell_holy_vision.c', 'spell_invalid.c', 'spell_invisibility.c',
        'spell_poison_cloud.c', 'spell_rain_of_fire.c'])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src', 'spell'), [
        'spell_cast_next_order_reference.c', 'spell_cast_order_reference.c',
        'spell_heal_reference.c', 'spell_raise_dead_reference.c',
        'spell_summon_reference.c', 'spell_unholy_armor_reference.c'])


def test_spell_heal():
    cases = []
    for ttype in (0x05, 0x1c, 0x20, 0x32, 0x33):
        for hp in (1, 10, 50):
            for mana in (0, 2, 30, 255):
                for cast in (0, 1):
                    cases.append(T4Case(
                        args=(U, cast),
                        mem={U: mk({0x1a: (1, mana), 0x52: (4, T)}),
                             T: mk({0x16: (2, hp), 0x1b: (1, ttype)})},
                        label=f"t{ttype} hp{hp} m{mana} c{cast}"))
    t4spec.run_spec(f('spell_heal_reference.c'), 'SpellHeal_', 0x27670, cases,
                    watch=[(U, 0x5c), (T, 0x5c)],
                    stubs=[T4Stub(0x11ec0, log_regs=('eax', 'edx'))],
                    init_emu=map_arena)


def test_spell_holy_vision():
    cases = []
    for mana in (0, 0x31, 0x32, 0xff):
        for cast in (0, 1):
            cases.append(T4Case(
                args=(U, cast),
                mem={U: mk({0x1a: (1, mana), 0x1e: (1, 3),
                            0x4c: (4, 0x00050000), 0x4e: (4, 0x00070000)})},
                label=f"m{mana} c{cast}"))
    t4spec.run_spec(f('spell_holy_vision.c'), 'SpellHolyVision_', 0x27740, cases,
                    watch=[(U, 0x5c)],
                    stubs=[T4Stub(0x2e9c4, log_regs=('eax', 'edx', 'ebx')),
                           T4Stub(0x11e70, log_regs=('eax', 'edx', 'ebx'))],
                    init_emu=map_arena)


def test_spell_unholy_armor():
    cases = []
    for mana in (0, 0x7c, 0x7d, 0xff):
        for hp in (1, 0x1e, 0x1f, 100):
            for cast in (0, 1):
                cases.append(T4Case(
                    args=(U, cast),
                    mem={U: mk({0x1a: (1, mana), 0x52: (4, T)}),
                         T: mk({0x16: (2, hp)})},
                    label=f"m{mana} hp{hp} c{cast}"))
    t4spec.run_spec(f('spell_unholy_armor_reference.c'), 'SpellUnholyArmor_', 0x277d4, cases,
                    watch=[(U, 0x5c), (T, 0x5c)],
                    stubs=[T4Stub(0x11ec0, log_regs=('eax', 'edx'))],
                    init_emu=map_arena)


def test_spell_raise_dead():
    cases = []
    for mana in (0, 0x45, 0x46, 0xff):
        for cast in (0, 1):
            cases.append(T4Case(
                args=(U, cast),
                mem={0x59640: ARR.to_bytes(4, 'little'),
                     U: mk({0x1a: (1, mana), 0x0a: (2, 10), 0x0c: (2, 10), 0x1e: (1, 1)}),
                     ARR: b'\x00' * (0x5c * 200),
                     ARR + 0x5c: mk({0x1b: (1, 0x33), 0x10: (2, 2),
                                     0x0a: (2, 11), 0x0c: (2, 11), 0x08: (1, 4)})},
                label=f"m{mana} c{cast}"))
    t4spec.run_spec(f('spell_raise_dead_reference.c'), 'SpellRaiseDead_', 0x278ac, cases,
                    watch=[(U, 0x5c), (ARR, 0x5c * 3), (0x5a7c8, 1)],
                    stubs=[T4Stub(0x2e6f4, ret=1, log_regs=('eax', 'edx', 'ebx', 'ecx')),
                           T4Stub(0x1bee4, log_regs=('eax', 'edx'))],
                    init_emu=map_arena)


def test_spell_summon():
    cases = []
    for spell in (0x16, 0x17, 0x19, 0x10):
        for mana in (0, 0x3b, 0x3c, 0xff):
            for cast in (0, 1):
                cases.append(T4Case(
                    args=(U, cast),
                    mem={U: mk({0x1a: (1, mana), 0x1b: (1, 2), 0x1e: (1, 1),
                                0x1f: (1, spell), 0x08: (4, 0x00030000),
                                0x0a: (4, 0x00040000)})},
                    label=f"s{spell:x} m{mana} c{cast}"))
    t4spec.run_spec(f('spell_summon_reference.c'), 'SpellSummon_', 0x279c0, cases,
                    watch=[(U, 0x5c)],
                    stubs=[T4Stub(0x2e650, ret=1, stack_pop=4,
                                  log_regs=('eax', 'edx', 'ebx', 'ecx'))],
                    init_emu=map_arena)


def test_spell_cast_order():
    for ret in (0, 1):
        cases = [T4Case(args=(U,),
                        mem={U: mk({0x1a: (1, 5), 0x1f: (1, 0)})},
                        label=f"r{ret}")]
        t4spec.run_spec(f('spell_cast_order_reference.c'), 'SpellCastOrder_', 0x27aa4, cases,
                        out_regs=(), watch=[(U, 0x5c)],
                        stubs=[T4Stub(0x27a8c, ret=ret, log_regs=('eax', 'edx')),
                               T4Stub(0x2ee50, ret=0, log_regs=('eax', 'edx'))],
                        init_emu=map_arena)


def test_spell_cast_next_order():
    cases = []
    for spell in (0, 0x1a):
        cases.append(T4Case(args=(U,),
                            mem={U: mk({0x1a: (1, 5), 0x1f: (1, spell)})},
                            label=f"s{spell:x}"))
    t4spec.run_spec(f('spell_cast_next_order_reference.c'), 'SpellCastNextOrder_', 0x27adc, cases,
                    out_regs=(), watch=[(U, 0x5c)],
                    stubs=[T4Stub(0x27a8c, ret=1, log_regs=('eax', 'edx')),
                           T4Stub(0x2eed4, log_regs=('eax', 'edx')),
                           T4Stub(0x2eeac, log_regs=('eax', 'edx'))],
                    init_emu=map_arena)
