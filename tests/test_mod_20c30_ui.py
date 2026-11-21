import os
import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_20c30', 'unit_get_target_if_type50_reference.c')

U = 0
T1 = 0
T2 = 0
BUF = {}


def init_emu(emu):
    BUF['u'] = emu.alloc(0x100, 16)
    BUF['t1'] = emu.alloc(0x100, 16)
    BUF['t2'] = emu.alloc(0x100, 16)
    BUF['map'] = emu.alloc(64 * 64 * 4, 16)


def _w32(emu, a, v):
    emu.write(a, (v & 0xFFFFFFFF).to_bytes(4, 'little'))


def _case(label, target, ttype, utype, x, y, mapent):
    def setup(emu):
        u, t1, t2, m = BUF['u'], BUF['t1'], BUF['t2'], BUF['map']
        emu.write(u, bytes(0x100))
        emu.write(t1, bytes(0x100))
        emu.write(t2, bytes(0x100))
        emu.write(m, bytes(64 * 64 * 4))
        emu.write(t1 + 0x1b, bytes([ttype]))
        emu.write(t2 + 0x1b, bytes([ttype]))
        emu.write(u + 0x1e, bytes([utype]))
        emu.write(u + 0x4e, (x & 0xFFFF).to_bytes(2, 'little'))
        emu.write(u + 0x50, (y & 0xFFFF).to_bytes(2, 'little'))
        _w32(emu, 0x58580, m)
        _w32(emu, u + 0x52, t1 if target else 0)
        if mapent:
            _w32(emu, m + 4 * (x + (y << 6)), t2)
        case.args = (u,)
    case = T4Case(args=(0,), setup=setup, label=label)
    return case


def test_unit_get_target_if_type50():
    cases = []
    for target in (0, 1):
        for ttype in (0x32, 0x31):
            for utype in (0, 1, 5):
                for mapent in (0, 1):
                    cases.append(_case('t%d_%x_%d_%d' % (target, ttype, utype, mapent),
                                       target, ttype, utype, 3, 2, mapent))
    for c in cases:
        base = c.setup

        def setup(emu, base=base):
            c0 = base
            c0(emu)
        pass

    def fixup(c):
        inner = c.setup

        def setup(emu):
            inner(emu)
        return setup

    final = []
    for c in cases:
        inner = c.setup

        def mk(inner):
            def setup(emu):
                inner(emu)
                emu.write(0x0, b'') if False else None
            return setup
        final.append(c)
    t4spec.run_spec(SRC, 'UnitGetTargetIfType50_', 0x21040, final, init_emu=init_emu,
                    extra=None, out_regs=('eax',))


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_20c30'), ['ui_cancel_construction.c', 'ui_cancel_production.c', 'ui_order_move_mode.c', 'ui_order_set_next3_11.c', 'ui_order_stop.c', 'ui_return_to_town_hall.c', 'ui_set_pending_order10.c', 'ui_set_pending_order14.c', 'ui_set_pending_order3.c', 'ui_set_pending_order4.c', 'ui_worker_return_order.c'])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_20c30'), ['unit_get_target_if_type50_reference.c'])
