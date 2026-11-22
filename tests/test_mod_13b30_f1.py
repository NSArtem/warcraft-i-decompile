import os
import struct

import pytest

from wc1 import t4spec
from wc1 import path

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

BLD = 0x58e1e
MEN = 0x58e28
UTC = 0x51338
CB = 0x51408
CB_ADDR = 0x13b30


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_13b30'), ['count_building_delta.c', 'count_food_building_delta.c', 'count_men_delta.c', 'count_town_hall_delta.c', 'count_town_hall_full_delta.c'])


def test_reference_near_miss():
    t4spec.assert_ref_mismatch(path('src/mod_13b30'), ['player_stats_reset_reference.c', 'unit_count_add_reference.c', 'unit_count_remove_reference.c'])


PARAMS = []
for _t in (0, 1, 0x1f, 0x20, 0x25, 0x32, 0x33, 0x2b):
    for _o in (0, 3, 4):
        for _fl in (0x0000, 0x0080, 0x1180, 0x007f):
            for _ctr in (0, 1):
                for _cb in (0, 1):
                    PARAMS.append((_t, _o, _fl, _ctr, _cb))


def _unit_spec(src, name, addr):
    state = {}
    watch = []

    def init_emu(emu):
        state["unit"] = emu.alloc(64, 16)
        state["ctr"] = emu.alloc(16, 16)
        watch[:] = [(BLD, 10), (MEN, 8), (state["ctr"], 16)]

    idx = [0]

    def gen(rng):
        t, o, fl, ctr, cb = PARAMS[idx[0] % len(PARAMS)]
        idx[0] += 1
        u = state["unit"]
        cp = state["ctr"]

        def setup(emu):
            emu.write(u, bytes(64))
            emu.write(u + 0x10, struct.pack("<H", fl))
            emu.write(u + 0x1b, bytes([t]))
            emu.write(u + 0x1e, bytes([o]))
            emu.write(BLD, struct.pack("<5H", 10, 20, 30, 40, 50))
            emu.write(MEN, struct.pack("<4H", 100, 200, 300, 400))
            emu.write(cp, struct.pack("<8H", 5, 6, 7, 8, 9, 0, 0, 0))
            emu.write(UTC + t * 4, struct.pack("<I", cp if ctr else 0))
            emu.write(CB + t * 4, struct.pack("<I", CB_ADDR if cb else 0))

        from wc1.t4spec import T4Case
        return T4Case(args=(u,), setup=setup, label="p%d" % (idx[0] - 1))

    t4spec.run_spec(src, name, addr, watch=watch,
                    stubs=[t4spec.T4Stub(CB_ADDR, log_regs=("eax", "edx"))],
                    out_regs=(), init_emu=init_emu, rand_cases=len(PARAMS),
                    rand_gen=gen)


def test_unit_count_add():
    _unit_spec('src/mod_13b30/unit_count_add_reference.c', 'UnitCountAdd_', 0x13c04)


def test_unit_count_remove():
    _unit_spec('src/mod_13b30/unit_count_remove_reference.c', 'UnitCountRemove_', 0x13c84)


def test_player_stats_reset():
    from wc1.t4spec import T4Case

    def fill(emu):
        emu.write(0x58db0, b"\xaa" * 0x9c)
        emu.write(0x50d84, b"\xbb" * 0x70)
        emu.write(0x50e68, b"\xcc" * 20)

    cases = [T4Case(args=(k,), setup=fill, label="keep=%d" % k) for k in (0, 1, 2, -1)]
    t4spec.run_spec('src/mod_13b30/player_stats_reset_reference.c', 'PlayerStatsReset_', 0x13d04,
                    cases=cases,
                    watch=[(0x58db0, 0x9c), (0x50d84, 0x70), (0x50e68, 20)],
                    out_regs=())
