import os
import re
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM',
)

SRC = path('src/mod_2ced0')
T3_FILES = ['unit_advance_order.c']
REF_FILES = [
    'draw_list_rebuild_reference.c',
    'unit_draw_sprite_reference.c',
    'unit_order_target_reference.c',
    'unit_set_order_reference.c',
    'unit_target_relation_reference.c',
    'unit_update_all_reference.c',
    'units_init_game_reference.c',
]

_BL = {}
REGS = ("eax", "edx", "ebx", "ecx")
DUMMY = 0x106e8  # NopCallback, used as harmless callback target


def _by():
    if not _BL:
        _BL.update(t4spec.by_link_lenient())
    return _BL


def A(name):
    b = _by()
    for e in b.values():
        if e.get('name') == name:
            return e['addr']
    for k in (name, name + '_', '_' + name):
        if k in b:
            return b[k]['addr']
    m = re.fullmatch(r"(?:fn|dat)_([0-9a-fA-F]+)", name)
    if m:
        return int(m.group(1), 16)
    raise KeyError(name)


def pk(f, *v):
    return struct.pack('<' + f, *v)


def rs(rng, n, lo, hi):
    return pk('%dh' % n, *[rng.randrange(lo, hi) for _ in range(n)])


def UB(fields):
    b = bytearray(0x47e0)
    for i, d in fields.items():
        for off, (f, v) in d.items():
            struct.pack_into('<' + f, b, i * 0x5c + off, v)
    return bytes(b)


def S(addr, n, ret=0):
    return T4Stub(addr, ret=ret, log_regs=REGS[:n])


class Lazy(object):
    def __init__(self, f):
        self.f = f

    def __iter__(self):
        return iter(self.f())


def memset_stub():
    def fn(e, log):
        s, c, n = e.reg('eax'), e.reg('edx'), e.reg('ebx')
        log(s, c & 0xff, n)
        e.write(s, bytes([c & 0xff]) * n)
        return s
    return T4Stub(A('memset'), fn=fn)


def grp_stub(addr, vals):
    def fn(e, log):
        sp = e.reg('esp')
        ya, mwa, mha = struct.unpack('<3I', e.read(sp + 4, 12))
        e.write(e.reg('ebx'), pk('6h', *vals[0]))
        e.write(e.reg('ecx'), pk('h', vals[1]))
        e.write(ya, pk('h', vals[2]))
        e.write(mwa, pk('h', vals[3]))
        e.write(mha, pk('h', vals[4]))
        log(e.reg('eax'), e.reg('edx') & 0xff)
    return T4Stub(addr, fn=fn, stack_pop=12)


def run(fname, cfile, addr, makers, stubs=None, watch=None, out_regs=(), ptrs=()):
    st = {}

    def init(emu):
        st['u'] = emu.alloc(0x47e0, 16)
        st['o'] = emu.alloc(0x1000, 16)
        st['aux'] = emu.alloc(0x400, 16)
        for nm, key, off in ptrs:
            emu.write(A(nm), pk('I', st[key] + off))

    it = iter(makers)

    def gen(rng):
        return next(it)(st, rng)

    def wl():
        w = [(st['u'], 0x47e0), (st['aux'], 0x400)]
        if watch:
            w += watch(st)
        return w

    sl = stubs(st) if stubs else []
    t4spec.run_spec(
        os.path.join(SRC, cfile), fname, addr, (), watch=Lazy(wl),
        stubs=sl, out_regs=out_regs, init_emu=init,
        rand_cases=len(makers), rand_gen=gen, log_cap=4096,
    )


def test_t3_files_match():
    if T3_FILES:
        t4spec.assert_t3_matches(path('src/mod_2ced0'), T3_FILES)


def test_ref_files_still_mismatch():
    if REF_FILES:
        t4spec.assert_ref_mismatch(path('src/mod_2ced0'), REF_FILES)


def test_draw_list_rebuild():
    def mk(st, rng):
        f = {}
        for i in range(200):
            f[i] = {0x10: ('H', rng.choice([0, 1, 2, 4, 5, 7, 8, 0x200, 0x201, 0x205, 0x207]))}
        return T4Case(mem={st['u']: UB(f)})
    run(
        'DrawListRebuild_', 'draw_list_rebuild_reference.c', 0x2d058, [mk] * 4,
        stubs=lambda st: [S(A('DrawListInsert'), 1), S(0x13c04, 1)],
        ptrs=(('unit_array', 'u', 0),),
    )


def test_unit_update_all():
    def mk(st, rng):
        f = {}
        for i in range(12):
            f[i] = {
                0x10: ('H', rng.choice([0, 0, 0x80, 1])),
                0x1b: ('B', rng.randrange(0x1c, 0x36)),
                0x16: ('H', rng.randrange(0, 400)),
                0x4e: ('B', rng.choice([0, 1, 2])),
                0x4c: ('h', rng.choice([1, 2, 5])),
            }
        mem = {
            st['u']: UB(f),
            A('unit_max_hp'): pk('54H', *[rng.randrange(1, 400) for _ in range(54)]),
            A('cheat_flags'): pk('I', rng.choice([0, 2])),
        }
        return T4Case(mem=mem)
    run(
        'UnitUpdateAll_', 'unit_update_all_reference.c', 0x2d204, [mk] * 5,
        stubs=lambda st: [S(A('UnitUpdateDamageFrame'), 1), S(A('UnitStartDeath'), 1)],
        ptrs=(('unit_array', 'u', 0), ('damage_fire_heavy', 'aux', 0x100), ('damage_fire_light', 'aux', 0x200)),
    )


def test_units_init_game():
    def mkc(posmode):
        def f(st, rng):
            pos = st['aux'] if posmode else 0
            mem = {A('unit_type_size'): rs(rng, 104, 1, 30)}
            return T4Case(args=(pos,), mem=mem)
        return f

    def stubs(st):
        return [
            memset_stub(),
            T4Stub(A('fn_11f78'), fn=lambda e, log: (log(e.reg('eax')), st['aux'] + 0x100 + e.reg('eax') * 0x10)[1]),
            T4Stub(A('SaveReadStream'), fn=lambda e, log: (log(e.reg('eax'), e.reg('edx'), e.reg('ebx')), e.reg('ebx') + 4)[1]),
            S(A('SaveRelocUnits'), 1),
            S(A('SaveRelocObjects'), 1),
            S(A('DrawListRebuild'), 0),
        ]
    run(
        'UnitsInitGame_', 'units_init_game_reference.c', 0x2d4b8,
        [mkc(0), mkc(1), mkc(0)], stubs=stubs, out_regs=('eax',),
        watch=lambda st: [
            (st['o'], 0xed8), (A('draw_list'), 0x324), (A('unit_half_size'), 0xd0),
            (A('damage_fire_heavy'), 4), (A('damage_fire_light'), 4), (A('spell_order'), 2),
            (A('pending_order'), 2), (A('map_cursor_flags'), 1),
        ],
        ptrs=(('unit_array', 'u', 0), ('object_array', 'o', 0)),
    )


def test_unit_draw_sprite():
    def mkc(x, y, sx, sy, d, sfl=0):
        def f(st, rng):
            u = st['u']
            mem = {
                u: UB({0: {0: ('B', 3), 1: ('B', sfl), 6: ('h', x), 8: ('h', y), 0xd: ('B', 5), 0xe: ('B', d)}}),
                A('dat_522a8') + 12: pk('I', 0x12345),
                A('dat_552a8'): pk('16b', *[rng.randrange(-3, 4) for _ in range(16)]),
                A('sprite_blitters'): pk('8I', *([DUMMY] * 8)),
            }
            return T4Case(args=(u, sx & 0xffff, sy & 0xffff), mem=mem)
        return f

    def blit(e, log):
        r = struct.unpack('<4H', e.read(e.reg('ecx'), 8))
        log(e.reg('eax') & 0xffff, e.reg('edx') & 0xffff, *r)

    def stubs(st):
        return [
            grp_stub(A('GrpFrameInfo'), ((16, 20, 0, 0, 0, 0), -2, -3, 20, 24)),
            T4Stub(DUMMY, fn=blit),
        ]
    run(
        'UnitDrawSprite_', 'unit_draw_sprite_reference.c', 0x2d704,
        [mkc(100, 80, 0, 0, 2), mkc(10, 10, 20, 20, 0), mkc(500, 80, 0, 0, 1),
         mkc(100, 300, 0, 0, 3), mkc(230, 170, 0, 0, 7), mkc(100, 80, 0, 0, 2, 1),
         mkc(-40, 50, 0, 0, 4)],
        stubs=stubs,
    )


def test_unit_order_target():
    def mkc(order, tgt):
        def f(st, rng):
            u = st['u']
            mem = {u: UB({0: {0x1f: ('B', order), 0x11: ('B', 0x5a), 9: ('B', 7)},
                          1: {0xa: ('I', rng.getrandbits(32))}})}
            t = u + 0x5c if tgt else 0
            return T4Case(args=(u, rng.randrange(0, 0x7fff), rng.randrange(0, 0x7fff), t),
                          stack_args=(DUMMY,), mem=mem)
        return f
    run(
        'UnitOrderTarget_', 'unit_order_target_reference.c', 0x2e100,
        [mkc(o, t) for o in (0, 1, 2, 12, 5) for t in (0, 1)],
        stubs=lambda st: [S(A('UnitOrderTargetFinish'), 1), S(DUMMY, 1)],
    )


def test_unit_target_relation():
    def mkc(order, p):
        def f(st, rng):
            u = st['u']
            mem = {
                u: UB({0: {0x1e: ('B', 2), 0x1f: ('B', order), 0x52: ('I', u + 0x5c if p else 0)},
                       1: {0x1e: ('B', 3)}}),
                A('dat_55264'): bytes([0, 1, 2, 3, 0, 1, 2, 3] + [1] * 24),
                A('hostility'): bytes(rng.randrange(0, 4) for _ in range(25)),
            }
            return T4Case(args=(u,), mem=mem)
        return f
    run(
        'UnitTargetRelation_', 'unit_target_relation_reference.c', 0x2e9f4,
        [mkc(o, p) for o in range(8) for p in (0, 1)], out_regs=('eax',),
    )


def test_unit_set_order():
    def mkc(flags, b1b, order):
        def f(st, rng):
            u = st['u']
            mem = {
                u: UB({0: {0x10: ('H', flags | 0xc000), 0x1b: ('B', b1b), 0x52: ('I', 0x1234), 0x1f: ('B', 9)}}),
                A('order_sound'): bytes(rng.randrange(256) for _ in range(32)),
            }
            return T4Case(args=(u, order), mem=mem)
        return f
    run(
        'UnitSetOrder_', 'unit_set_order_reference.c', 0x2ee50,
        [mkc(fl, b, o) for fl in (0, 2) for b in (5, 0x25) for o in (2, 7)],
        stubs=lambda st: [S(A('UnitStartAnim'), 2)],
    )
