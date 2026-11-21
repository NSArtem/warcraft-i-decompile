import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_2ced0')
REF = os.path.join(SRC, 'unit_start_death_reference.c')
USZ = 0x5C
NUNITS = 200


def test_ref_mismatch_guard():
    t4spec.assert_ref_mismatch(SRC, ['unit_start_death_reference.c'])


def _addr(name):
    bl = t4spec.by_link_lenient()
    for k in (name + '_', '_' + name, name):
        if k in bl:
            return bl[k]['addr']
    raise KeyError(name)


def _unit(b7=0, flags=0, b1a=0, typ=0, b1c=0, owner=0, s4c=0, s4e=0, s50=0, s52=0, ptr52=None):
    b = bytearray(USZ)
    b[7] = b7
    struct.pack_into('<H', b, 0x10, flags)
    b[0x1a] = b1a
    b[0x1b] = typ
    b[0x1c] = b1c
    b[0x1e] = owner
    struct.pack_into('<hhhh', b, 0x4c, s4c, s4e, s50, s52)
    if ptr52 is not None:
        struct.pack_into('<I', b, 0x52, ptr52)
    return b


def _make_case(label, ukw, others=()):
    """Unit under test lives at index 5; `others` is {index: kwargs}."""
    def setup(emu):
        arr = ST['arr']
        ua = arr + 5 * USZ
        data = bytearray(USZ * NUNITS)
        kw = dict(ukw)
        data[5 * USZ:6 * USZ] = _unit(**kw)
        for idx, okw in others:
            okw = dict(okw)
            if okw.pop('ptr_u', False):
                okw['ptr52'] = ua
            data[idx * USZ:(idx + 1) * USZ] = _unit(**okw)
        emu.write(arr, bytes(data))
        emu.write(_addr('unit_array'), struct.pack('<I', arr))
        emu.write(_addr('status_dirty'), b'\x00\x00')
        emu.write(0x50d98, struct.pack('<8h', 5, 6, 7, 8, 9, 10, 11, 12))
        ST['ua'] = ua
    c = t4spec.T4Case(args=(0,), setup=setup, label=label)
    return c


ST = {}
W = []


def _init(emu):
    ST['arr'] = emu.alloc(USZ * NUNITS, 16)
    del W[:]
    W.append((ST['arr'], USZ * NUNITS))
    W.append((0x50d98, 16))
    W.append((_addr('status_dirty'), 2))


def _cases():
    out = []
    # progress branch: s52+1 < s50
    out.append(_make_case('progress', dict(s50=10, s52=3, s4e=4, b1a=7)))
    out.append(_make_case('progress_big', dict(s50=300, s52=1, s4e=4)))
    # equal: returns early
    out.append(_make_case('equal', dict(s50=4, s52=3, b1a=1)))
    # over: full path, no match in list
    out.append(_make_case('over_nomatch', dict(s50=3, s52=5, typ=2, owner=3, flags=0x10)))
    # over: match at index 9
    out.append(_make_case('over_match', dict(s50=3, s52=5, typ=4, owner=2, s4e=9, flags=0x10),
                          [(9, dict(flags=0x8, ptr_u=True))]))
    # over: candidate blocked by 0x200 flag, later candidate matches
    out.append(_make_case('over_blocked', dict(s50=3, s52=5, typ=7, owner=1, s4e=2),
                          [(1, dict(flags=0x208, ptr_u=True)),
                           (150, dict(flags=0x8, ptr_u=True))]))
    # candidate without flag 8
    out.append(_make_case('over_noflag8', dict(s50=3, s52=5, typ=1, owner=0),
                          [(3, dict(flags=0x0, ptr_u=True))]))
    return out


def _stubs():
    a1 = [_addr('SndConstructionTick'), _addr('SndWorkComplete'),
          0x13c04, 0x13c84, 0x1c9c0, 0x1cf94]
    a2 = [0x26360, 0x2e5c8]
    return ([T4Stub(a, log_regs=('eax',)) for a in a1] +
            [T4Stub(a, log_regs=('eax', 'edx')) for a in a2])


def _fix(cases):
    # unit pointer arg is only known after init_emu; patch via regs_in at run time
    for c in cases:
        inner = c.setup

        def wrap(emu, inner=inner, c=c):
            inner(emu)
            c.regs_in = {'eax': ST['ua']}
        c.setup = wrap
    return cases


def test_unit_start_death():
    t4spec.run_spec(REF, 'UnitStartDeath_', 0x2d0e0, _fix(_cases()),
                    watch=W, stubs=_stubs(), out_regs=(), init_emu=_init)
