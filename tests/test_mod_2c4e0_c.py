import os
import struct
import random

import pytest

from wc1 import path, t4spec

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_2c4e0')

_FUNCS, _DATAS = t4spec.load_lenient()


def A(name):
    """Address of a named data symbol (or dat_XXXXX placeholder)."""
    for e in _DATAS.values():
        if e["name"] == name:
            return e["addr"]
    if name.startswith("dat_"):
        return int(name[4:], 16)
    raise KeyError(name)


def F(name):
    for e in _FUNCS.values():
        if e["name"] == name:
            return e["addr"]
    raise KeyError(name)


def put(emu, name, fmt, *v):
    emu.write(A(name), struct.pack(fmt, *v))


def mkcase(label, build):
    """Case whose args are computed inside setup (after init_emu allocations exist)."""
    c = t4spec.T4Case(label=label)

    def setup(emu):
        c.args = build(emu)
    c.setup = setup
    return c


def make_init(S, W, globs=()):
    def init(emu):
        S['flags'] = emu.alloc(8192, 16)
        S['cost'] = emu.alloc(8192, 16)
        S['objmap'] = emu.alloc(16384, 16)
        S['owners'] = emu.alloc(64, 16)
        S['unit'] = emu.alloc(0x100, 16)
        S['pathbuf'] = emu.alloc(64, 16)
        S['pt'] = emu.alloc(16, 16)
        S['cnt'] = emu.alloc(16, 16)
        W[:] = [(S['flags'], 8192), (S['cost'], 8192), (S['pathbuf'], 64),
                (S['cnt'], 16), (S['unit'], 0x100)]
        for g, n in globs:
            W.append((A(g), n))
    return init


def setup_maps(emu, S, rng):
    emu.write(S['flags'], bytes(rng.randrange(256) & (0xff if i % 2 == 0 else 0xfe)
                                for i in range(8192)))
    emu.write(S['cost'], bytes(rng.randrange(8) for _ in range(8192)))
    put(emu, 'map_flags', '<I', S['flags'])
    put(emu, 'map_cost', '<I', S['cost'])
    put(emu, 'object_map', '<I', S['objmap'])


def test_t3_files_still_match():
    files = ['path_advance_facing.c', 'path_distance.c', 'path_needs_path.c']
    if files:
        t4spec.assert_t3_matches(SRC, files)


def test_reference_files_still_mismatch():
    files = ['path_block_area_reference.c', 'path_cost_walk_reference.c',
             'path_find_reference.c', 'path_store_steps_reference.c',
             'path_trace_reference.c']
    if files:
        t4spec.assert_ref_mismatch(SRC, files)


def test_path_cost_walk():
    S, W = {}, []
    init = make_init(S, W)

    def mk(sx, sy, tx, ty):
        def build(emu):
            rng = random.Random(1)
            put(emu, 'path_start', '<hh', sx, sy)
            put(emu, 'map_cost', '<I', S['cost'])
            emu.write(S['pt'], struct.pack('<hh', tx, ty))
            dx = struct.unpack('<8b', emu.read(A('dir_dx'), 8))
            dy = struct.unpack('<8b', emu.read(A('dir_dy'), 8))
            sg = lambda v: (v > 0) - (v < 0)
            buf = bytearray(8192)
            for y in range(64):
                for x in range(64):
                    wx, wy = sg(tx - x), sg(ty - y)
                    d = 0
                    for k in range(8):
                        if dx[k] == wx and dy[k] == wy:
                            d = k
                            break
                    buf[(y * 64 + x) * 2] = d
                    buf[(y * 64 + x) * 2 + 1] = rng.randrange(8)
            emu.write(S['cost'], bytes(buf))
            return (S['pt'], S['pt'])
        return mkcase('walk %d,%d->%d,%d' % (sx, sy, tx, ty), build)

    cases = [mk(2, 3, 10, 8), mk(5, 5, 5, 0), mk(0, 0, 7, 7), mk(9, 9, 9, 9),
             mk(30, 2, 3, 40)]
    t4spec.run_spec(path('src/mod_2c4e0/path_cost_walk_reference.c'),
                    'PathCostWalk_', 0x2c790, cases, init_emu=init, watch=W)


def test_path_store_steps():
    S, W = {}, []
    init = make_init(S, W)

    def mk(count, direction, sx=3, sy=4, tx=9, ty=9):
        def build(emu):
            setup_maps(emu, S, random.Random(count * 7 + direction))
            put(emu, 'path_start', '<hh', sx, sy)
            emu.write(S['pt'], struct.pack('<hh', tx, ty))
            emu.write(S['pathbuf'], b'\x55' * 64)
            return (S['pathbuf'], count, S['pt'], direction)
        return mkcase('steps n=%d dir=%d' % (count, direction), build)

    cases = [mk(0, 0), mk(1, 0), mk(5, 1), mk(19, 0), mk(20, 1), mk(30, 0),
             mk(8, 1, 3, 4, 3, 4), mk(12, 0, 60, 60, 61, 61)]
    t4spec.run_spec(path('src/mod_2c4e0/path_store_steps_reference.c'),
                    'PathStoreSteps_', 0x2c8c0, cases, out_regs=(),
                    init_emu=init, watch=W)


def test_path_trace():
    S, W = {}, []
    init = make_init(S, W, [('dat_5a470', 4), ('path_dir', 1)])

    def dx_stub(e, log):
        e.write(e.reg('edx'), struct.pack('<hh', 1, 0))
        e.write(e.reg('ebx'), struct.pack('<hh', 0, 0))
        return 1

    def mk(n, mask, bmask, blocked):
        def build(emu):
            setup_maps(emu, S, random.Random(n + 31 * mask))
            emu.write(S['flags'], bytes(8192))
            for k in blocked:
                emu.write(S['flags'] + (4 * 64 + 4 + k) * 2, struct.pack('<H', bmask))
            emu.write(S['owners'], bytes(64))
            put(emu, 'dat_5a474', '<I', S['owners'])
            put(emu, 'path_start', '<hh', 4, 4)
            put(emu, 'path_dest', '<hh', 4 + n, 4)
            put(emu, 'dat_5a47e', '<h', 4)
            put(emu, 'path_block_mask', '<H', bmask)
            put(emu, 'path_dir', '<B', 7)
            emu.write(S['cnt'], b'\xaa' * 16)
            return (S['cnt'], mask)
        return mkcase('trace n=%d mask=%#x blocked=%s' % (n, mask, blocked), build)

    cases = [mk(3, 0xffff, 0x4, []), mk(25, 0xffff, 0x4, []),
             mk(5, 0x1fff, 0x4, [1]), mk(5, 0xffff, 0x8, [5]),
             mk(6, 0x1fff, 0x4, [2, 4]), mk(1, 0xffff, 0x4, [])]
    stubs = [t4spec.T4Stub(0x1df0c, log_regs=('eax', 'edx')),
             t4spec.T4Stub(0x1df94, fn=dx_stub)]
    t4spec.run_spec(path('src/mod_2c4e0/path_trace_reference.c'),
                    'PathTrace_', 0x2c958, cases, stubs=stubs,
                    init_emu=init, watch=W)


def test_path_block_area():
    S, W = {}, []
    init = make_init(S, W)

    def mk(mask, ux, uy, utype, use_unit, dest=(10, 10)):
        def build(emu):
            setup_maps(emu, S, random.Random(ux * 64 + uy))
            put(emu, 'path_dest', '<hh', dest[0], dest[1])
            put(emu, 'dat_5a47e', '<h', dest[1])
            emu.write(S['unit'], bytes(0x100))
            emu.write(S['unit'] + 0x0a, struct.pack('<hh', ux, uy))
            emu.write(S['unit'] + 0x1b, bytes([utype]))
            return (mask, S['unit'] if use_unit else 0)
        return mkcase('block m=%#x u=(%d,%d) t=%d %s' % (mask, ux, uy, utype, use_unit), build)

    cases = [mk(0xffff, 5, 5, 0, True), mk(0x1fff, 20, 30, 3, True),
             mk(0xff7f, 0, 0, 1, True), mk(0xffff, 63, 63, 5, True),
             mk(0x1fff, 0, 0, 0, False), mk(0xffff, 0, 0, 0, False, (10, 10)),
             mk(0xfeff, 0, 0, 0, False, (0, 63)), mk(0xfeff, 0, 0, 0, False, (63, 0))]
    t4spec.run_spec(path('src/mod_2c4e0/path_block_area_reference.c'),
                    'PathBlockArea_', 0x2cb2c, cases, out_regs=(),
                    init_emu=init, watch=W)


def test_path_find():
    S, W = {}, []
    init = make_init(S, W, [('path_start', 4), ('path_dest', 4),
                            ('path_block_mask', 2), ('path_distance', 2),
                            ('dat_5a474', 4)])

    def mk(label, idx=0, p0=0xfe, owner=0, utype=0, tile=0, t36=0, ns2=0,
           p3a=0, target=0, hostile_flag=1):
        def build(emu):
            setup_maps(emu, S, random.Random(owner + utype))
            u = S['unit']
            emu.write(u, bytes(0x100))
            emu.write(u + 0x0a, struct.pack('<hh', 7, 8))
            emu.write(u + 0x1b, bytes([utype]))
            emu.write(u + 0x1e, bytes([owner]))
            emu.write(u + 0x21, bytes([ns2]))
            emu.write(u + 0x22, bytes([p0]) + bytes([1] * 19))
            emu.write(u + 0x36, struct.pack('<H', t36))
            emu.write(u + 0x3a, struct.pack('<I', p3a))
            emu.write(u + 0x4c, struct.pack('<H', idx))
            emu.write(u + 0x4e, struct.pack('<hh', 20, 22))
            emu.write(u + 0x52, struct.pack('<I', target))
            emu.write(A('dat_5008c'), bytes([hostile_flag] * 5))
            put(emu, 'scenario_tileset_id', '<H', tile)
            return (u,)
        return mkcase(label, build)

    cases = [mk('early', idx=0, p0=3), mk('idx20', idx=20), mk('plain'),
             mk('owner1', owner=1, utype=0), mk('tileset', owner=1, tile=0xc6),
             mk('timer', owner=2, t36=5), mk('type2', owner=1, utype=2),
             mk('ns2', ns2=6, owner=3), mk('ns2p3a', ns2=6, owner=3, p3a=1),
             mk('target', target=0x1234, owner=0), mk('nohostile', owner=1, hostile_flag=0)]

    for tr, sc, nd, cost in [(0, 1, 0, 3), (0, 1, 0, 9), (0, 0, 0, 3),
                             (1, 1, 0, 3), (0, 1, 1, 9), (2, 1, 0, 9)]:
        stubs = [
            t4spec.T4Stub(F('PathPeekStep'), ret=1, log_regs=('eax',)),
            t4spec.T4Stub(F('PathScan'), ret=sc, log_regs=('eax',)),
            t4spec.T4Stub(0x2c790, ret=cost, log_regs=('eax',)),
            t4spec.T4Stub(0x2c8c0, ret=0, log_regs=('eax', 'edx', 'ecx')),
            t4spec.T4Stub(0x2c958, ret=tr, log_regs=('edx',)),
            t4spec.T4Stub(0x2cb2c, ret=0, log_regs=('eax', 'edx')),
            t4spec.T4Stub(F('PathDistance'), ret=5, log_regs=()),
            t4spec.T4Stub(F('PathNeedsPath'), ret=nd, log_regs=()),
        ]
        t4spec.run_spec(path('src/mod_2c4e0/path_find_reference.c'),
                        'PathFind_', 0x2cc54, cases, stubs=stubs,
                        init_emu=init, watch=W)
