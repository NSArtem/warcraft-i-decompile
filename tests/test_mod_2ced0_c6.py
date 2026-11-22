import os
import random
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM')

SRC_DIR = 'src/mod_2ced0'
USZ = 0x5c
NUNITS = 200

A_UNIT_ARRAY = 0x59640
A_MAP_FLAGS = 0x5857c
A_SCENARIO = 0x50d82
A_TRAIN = 0x50d84
A_D98 = 0x50d98
A_WAVE = 0x50e4a
A_SITE = 0x50e54
A_HELPER = 0x50e5e
A_5008C = 0x5008c
A_STATUS = 0x5a2d0
A_5A7C2 = 0x5a7c2
A_NETPLAY = 0x52586
A_SUMMON = 0x5a7c8
A_51DF0 = 0x51df0

H = {}


def test_t3_and_nearmiss_guard():
    t4spec.assert_ref_mismatch(path(SRC_DIR),
                               ['unit_create_reference.c', 'unit_remove_reference.c'])


def _w16(b, off, v):
    struct.pack_into('<H', b, off, v & 0xFFFF)


def _w32(b, off, v):
    struct.pack_into('<I', b, off, v & 0xFFFFFFFF)


# ---------------------------------------------------------------- UnitRemove
def _remove_watch():
    return []


REMOVE_WATCH = []


def _init_remove(emu):
    H['arr'] = emu.alloc(NUNITS * USZ, 16)
    H['map'] = emu.alloc(0x2000, 16)
    H['ptr'] = emu.alloc(16, 16)
    REMOVE_WATCH[:] = [
        (H['arr'], NUNITS * USZ), (H['map'], 0x2000), (H['ptr'], 16),
        (A_STATUS, 2), (A_WAVE, 4), (A_SITE, 10), (A_HELPER, 10),
        (A_TRAIN, 10), (A_D98, 10),
    ]


UIDX = 3


def _remove_case(label, rng, **kw):
    f = dict(type=5, owner=1, flagsE=0, flags=0, b3e=0, s42=3, s44=2,
             useptr=False, scen=0, d5a7c2=0, d5008c=1, ptrval=0xFF,
             others=None, mapfill=0xFFFF)
    f.update(kw)

    def setup(emu):
        arr = H['arr']
        emu.write(arr, b'\x00' * (NUNITS * USZ))
        u = arr + UIDX * USZ
        # other units
        rr = random.Random(f['others'] if f['others'] is not None else 1)
        for i in range(NUNITS):
            if i == UIDX:
                continue
            b = bytearray(USZ)
            _w16(b, 0x10, rr.choice([0, 0, 8, 0x208, 0x207, 1, 0x10, 8 | 0x80]))
            b[0x1b] = rr.choice([5, 0x20, 0x26, 0x30, 0x0f])
            b[0x1e] = rr.randrange(5)
            _w16(b, 0xe, rr.choice([0, 0x10]))
            _w32(b, 0x52, rr.choice([0, u, u, arr + 7 * USZ]))
            emu.write(arr + i * USZ, bytes(b))
        b = bytearray(USZ)
        _w16(b, 0xe, f['flagsE'])
        _w16(b, 0x10, f['flags'])
        b[0x1b] = f['type']
        b[0x1e] = f['owner']
        b[0x3e] = f['b3e']
        _w16(b, 0x42, f['s42'])
        _w16(b, 0x44, f['s44'])
        _w32(b, 0x46, H['ptr'] if f['useptr'] else 0)
        emu.write(u, bytes(b))
        emu.write(H['ptr'], bytes([f['ptrval']]) + b'\x00' * 15)
        emu.write(H['map'], struct.pack('<H', f['mapfill']) * 0x1000)
        emu.write(A_UNIT_ARRAY, struct.pack('<I', arr))
        emu.write(A_MAP_FLAGS, struct.pack('<I', H['map']))
        emu.write(A_SCENARIO, struct.pack('<H', f['scen']))
        emu.write(A_5A7C2, struct.pack('<H', f['d5a7c2']))
        emu.write(A_5008C, bytes([0, f['d5008c'], f['d5008c'], f['d5008c'], f['d5008c']]))
        emu.write(A_STATUS, struct.pack('<H', 0))
        emu.write(A_WAVE, struct.pack('<I', 0))
        emu.write(A_SITE, struct.pack('<5H', 0, 0, 0, 0, 0))
        emu.write(A_HELPER, struct.pack('<5H', 0, 0, 0, 0, 0))
        emu.write(A_TRAIN, struct.pack('<5H', 9, 9, 9, 9, 9))
        emu.write(A_D98, struct.pack('<5H', 7, 7, 7, 7, 7))

    return T4Case(args=(0,), setup=lambda emu: (setup(emu), None)[1], label=label), f


def _remove_case_fixed_arg(label, rng, **kw):
    c, _ = _remove_case(label, rng, **kw)
    return c


def _remove_arg_setup(c):
    inner = c.setup

    def s(emu):
        inner(emu)

    return s


def _make_remove(label, rng, **kw):
    c, f = _remove_case(label, rng, **kw)
    inner = c.setup
    c.setup = inner
    return c


class _Lazy(T4Case):
    pass


def _build_cases_remove():
    rng = random.Random(0x2E14C)
    cases = []
    specs = [
        dict(type=0x10), dict(type=0x0f, owner=4), dict(type=0x0f, owner=1),
        dict(type=0x12), dict(type=0x11, owner=2), dict(type=5),
        dict(type=0x26, scen=0x82), dict(type=0x26, scen=1),
        dict(type=0x30, owner=2), dict(type=0x31, owner=1, d5008c=0),
        dict(type=0x20, owner=0), dict(type=0x20, owner=2, d5008c=1),
        dict(type=0x20, owner=2, d5008c=0),
        dict(type=0x21, owner=3, flagsE=0x10, useptr=True),
        dict(type=0x21, owner=3, flagsE=0x10, b3e=0x35),
        dict(type=0x21, owner=3, flagsE=0x10, b3e=0x10),
        dict(type=0x21, owner=3, flags=0x80), dict(type=0x21, owner=3, flags=0),
        dict(type=5, d5a7c2=1), dict(type=0x20, others=77),
    ]
    for i, s in enumerate(specs):
        cases.append((f'explicit[{i}]', s))
    for i in range(120):
        s = dict(
            type=rng.choice([5, 0x0f, 0x10, 0x11, 0x12, 0x1f, 0x20, 0x26, 0x30, 0x31, 0x35]),
            owner=rng.randrange(5), flagsE=rng.choice([0, 0x10]),
            flags=rng.choice([0, 0x80, 0x2]), b3e=rng.choice([0, 0x35, 7]),
            s42=rng.randrange(64), s44=rng.randrange(64),
            useptr=rng.random() < 0.4, scen=rng.choice([0, 0x82]),
            d5a7c2=rng.choice([0, 0, 1]), d5008c=rng.choice([0, 1, 2]),
            ptrval=rng.randrange(256), others=rng.randrange(1000),
            mapfill=rng.randrange(0x10000))
        cases.append((f'rand[{i}]', s))
    return cases


def test_unit_remove():
    watch = []
    rng = random.Random(1)
    cases = []
    for label, s in _build_cases_remove():
        c, _ = _remove_case(label, rng, **s)
        c.args = ()
        cases.append((c, s))

    # argument is the unit pointer, known only after init_emu allocates the array
    class Holder:
        pass

    def init(emu):
        _init_remove(emu)
        watch[:] = REMOVE_WATCH
        for c, _ in cases:
            c.args = (H['arr'] + UIDX * USZ,)

    stubs = [
        T4Stub(0x25e58, log_regs=()),
        T4Stub(0x29ea8, log_regs=('eax',)),
        T4Stub(0x2ee50, log_regs=('eax', 'edx')),
        T4Stub(0x13c84, log_regs=('eax',)),
        T4Stub(0x13954, log_regs=('eax',)),
        T4Stub(0x1b954, log_regs=('eax',)),
        T4Stub(0x2f73c, log_regs=()),
        T4Stub(0x11f10, log_regs=('eax',)),
        T4Stub(0x1b92c, log_regs=()),
        T4Stub(0x11ddc, log_regs=('eax',)),
    ]
    t4spec.run_spec(
        'src/mod_2ced0/unit_remove_reference.c', 'UnitRemove_', 0x2e14c,
        [c for c, _ in cases], watch=watch, stubs=stubs, out_regs=(),
        init_emu=init, log_cap=4096)


# ---------------------------------------------------------------- UnitCreate
def _create_case(label, rng):
    f = dict(
        px=rng.randrange(0x10000), py=rng.randrange(0x10000),
        type=rng.choice([0, 1, 5, 9, 0xa, 0xe, 0x1a, 0x1f, 0x20, 0x32, 0x35, rng.randrange(0x36)]),
        owner=rng.choice([0, 1, 4, 7, rng.randrange(8)]),
        slot=rng.choice([0, 5, 199, None, rng.randrange(200)]),
        ret=rng.choice([0, 1, 1, 1]),
        d5a7c2=rng.choice([0, 0, 1]), net=rng.choice([0, 1]),
        summon=rng.randrange(256), salt=rng.randrange(1 << 16),
        tbl=rng.randrange(1 << 30))
    return f


def _mk_create(label, f):
    def setup(emu):
        arr = H['arr']
        b = bytearray(NUNITS * USZ)
        for i in range(NUNITS):
            _w16(b, i * USZ + 0x10, 0)
            b[i * USZ + 5] = 0xAA
        if f['slot'] is not None:
            _w16(b, f['slot'] * USZ + 0x10, 1)
        emu.write(arr, bytes(b))
        tr = random.Random(f['tbl'])
        emu.write(A_51DF0, bytes(tr.choice([0, 0, 0x33, 0x44]) for _ in range(0x36)))
        emu.write(A_UNIT_ARRAY, struct.pack('<I', arr))
        emu.write(A_5A7C2, struct.pack('<H', f['d5a7c2']))
        emu.write(A_NETPLAY, struct.pack('<H', f['net']))
        emu.write(A_SUMMON, bytes([f['summon']]))
        emu.write(A_D98, struct.pack('<5H', 3, 3, 3, 3, 3))
        H['ret'] = f['ret']
        H['salt'] = f['salt']

    return T4Case(args=(f['px'], f['py'], f['type'], f['owner']), setup=setup, label=label)


def test_unit_create():
    rng = random.Random(0x2E6F4)
    watch = []
    cases = []
    base = [
        dict(px=0x123, py=0x456, type=0x1a, owner=1, slot=0, ret=1, d5a7c2=0, net=0,
             summon=3, salt=1, tbl=5),
        dict(px=0x10, py=0x20, type=0x32, owner=2, slot=1, ret=1, d5a7c2=0, net=0,
             summon=3, salt=2, tbl=6),
        dict(px=0x10, py=0x20, type=0x32, owner=2, slot=1, ret=1, d5a7c2=0, net=1,
             summon=3, salt=2, tbl=6),
        dict(px=0x10, py=0x20, type=5, owner=4, slot=2, ret=1, d5a7c2=0, net=0,
             summon=3, salt=2, tbl=6),
        dict(px=0x10, py=0x20, type=5, owner=4, slot=2, ret=0, d5a7c2=0, net=0,
             summon=3, salt=2, tbl=6),
        dict(px=0x10, py=0x20, type=5, owner=4, slot=None, ret=1, d5a7c2=0, net=0,
             summon=3, salt=2, tbl=6),
    ]
    for i, f in enumerate(base):
        cases.append(_mk_create(f'explicit[{i}]', f))
    for i in range(150):
        cases.append(_mk_create(f'rand[{i}]', _create_case('', rng)))

    def init(emu):
        H['arr'] = emu.alloc(NUNITS * USZ, 16)
        watch[:] = [(H['arr'], NUNITS * USZ), (A_D98, 10)]

    def f13990(e, log):
        log(e.reg('eax'), e.reg('edx'), e.reg('ebx') & 0xFF)
        return H['ret']

    def f19478(e, log):
        a = e.reg('eax')
        log(a)
        return (a * 0x1234567 + H['salt']) & 0xFFFF

    stubs = [
        T4Stub(0x1379c, log_regs=('eax',)),
        T4Stub(0x13928, log_regs=('eax',)),
        T4Stub(0x13990, fn=f13990),
        T4Stub(0x13c04, log_regs=('eax',)),
        T4Stub(0x19478, fn=f19478),
        T4Stub(0x1c9c0, log_regs=('eax',)),
        T4Stub(0x29cf8, log_regs=('eax',)),
        T4Stub(0x2cfd8, log_regs=('eax',)),
        T4Stub(0x2ee50, log_regs=('eax', 'edx')),
        T4Stub(0x2eeac, log_regs=('eax', 'edx')),
    ]
    t4spec.run_spec(
        'src/mod_2ced0/unit_create_reference.c', 'UnitCreate_', 0x2e6f4,
        cases, watch=watch, stubs=stubs, out_regs=('eax',),
        init_emu=init, log_cap=4096)
