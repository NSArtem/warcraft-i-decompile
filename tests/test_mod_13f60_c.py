import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.emu import Emu
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

T3 = ['order_update_research.c', 'order_update_stop.c', 'save_file_finish.c',
      'dispatch_fatal_reference.c', 'order_update_death_reference.c',
      'order_update_gone_reference.c', 'order_update_join_reference.c']
REFS = ['order_update_produce_reference.c', 'order_update_repair_reference.c',
        'order_update_spell_reference.c', 'unit_idle_turn_reference.c',
        'unit_work_progress_reference.c']

ST = {}
_FMT = {1: "B", 2: "H", 4: "I"}


def sym(name):
    bl = t4spec.by_link_lenient()
    for n in (name, "_" + name, name + "_"):
        if n in bl:
            return bl[n]["addr"]
    raise KeyError(name)


def _init(emu):
    ST['u'] = emu.alloc(0x100, 16)
    ST['d'] = emu.alloc(0x100, 16)
    ST['m'] = emu.alloc(8192, 16)


def _fill(spec):
    b = bytearray(0x100)
    for off, (v, sz) in (spec or {}).items():
        b[off:off + sz] = struct.pack("<" + _FMT[sz], v & ((1 << (8 * sz)) - 1))
    return b


def C(label, u=None, d=None, g=None, extra=(), post=None):
    c = T4Case(label=label)

    def setup(emu):
        ub = _fill(u)
        if d is not None:
            ub[0x52:0x56] = struct.pack("<I", ST['d'])
            emu.write(ST['d'], bytes(_fill(d)))
        emu.write(ST['u'], bytes(ub))
        for a, bts in (g or {}).items():
            emu.write(a, bts)
        if post:
            post(emu)
        c.args = (ST['u'],) + tuple(extra)
    c.setup = setup
    return c


def go(fn, fname, addr, cases, stubs=(), glob=(), out=("eax",)):
    w = list(glob)

    def ini(emu):
        _init(emu)
        w.extend([(ST['u'], 0x100), (ST['d'], 0x100), (ST['m'], 8192)])
    t4spec.run_spec(path('src', 'mod_13f60', fname), fn, addr, cases,
                    watch=w, stubs=stubs, out_regs=out, init_emu=ini)


def test_t3_files_match():
    if T3:
        t4spec.assert_t3_matches(path('src/mod_13f60'), T3)


def test_refs_still_mismatch():
    if REFS:
        t4spec.assert_ref_mismatch(path('src/mod_13f60'), REFS)


def test_order_update_gone():
    go("OrderUpdateGone_", "order_update_gone_reference.c", 0x13f60,
       [C("a", {0x1b: (3, 1)})], [T4Stub(0x2e96c, log_regs=("eax",))])


def test_order_update_death():
    tab = 0x5156c
    cases = [
        C("t33", {0x1b: (0x33, 1), 0x10: (7, 2)}),
        C("t17", {0x1b: (0x17, 1)}, g={tab + 0x17: b"\x05"}),
        C("nosound", {0x1b: (5, 1), 0x10: (0xf, 2)}, g={tab + 5: b"\x00"}),
        C("sound", {0x1b: (5, 1), 0x1e: (1, 1)}, g={tab + 5: b"\x03"}),
    ]
    stubs = [T4Stub(0x11ec0, log_regs=("eax", "edx")), T4Stub(0x1c9c0, log_regs=("eax",)),
             T4Stub(0x26360, log_regs=("eax", "edx")), T4Stub(0x13860, log_regs=("eax",)),
             T4Stub(0x2ee50, log_regs=("eax", "edx"))]
    go("OrderUpdateDeath_", "order_update_death_reference.c", 0x13f68, cases, stubs)


def test_unit_idle_turn():
    cases = [C("f%d" % f, {0x08: (f, 1)}) for f in (0, 3, 7)]
    for r in (0, 2, 5):
        stubs = [T4Stub(0x19478, ret=r, log_regs=("eax",))]
        go("UnitIdleTurn_", "unit_idle_turn_reference.c", 0x13ff0, cases, stubs, out=())


def test_order_update_join():
    wt = sym("ai_wave_timer")
    sc = sym("ai_site_count")
    glob = [(0x500de, 1), (wt, 4), (sc, 10)]
    cases = [
        C("hp9t5", {0x16: (9, 2), 0x1b: (5, 1)}),
        C("hp9t2", {0x16: (9, 2), 0x1b: (2, 1)}),
        C("hp9t16", {0x16: (9, 2), 0x1b: (0x10, 1)}),
        C("hp3t5", {0x16: (3, 2), 0x1b: (5, 1)}),
        C("hp3t16", {0x16: (3, 2), 0x1b: (0x10, 1)}),
        C("hp3t15", {0x16: (3, 2), 0x1b: (0xf, 1)}),
    ]
    for r in (0, 1):
        stubs = [T4Stub(0x13a90, ret=r, log_regs=("eax",)), T4Stub(0x13c84, log_regs=("eax",)),
                 T4Stub(0x13c04, log_regs=("eax",)), T4Stub(0x1c9c0, log_regs=("eax",)),
                 T4Stub(0x13ff0, log_regs=("eax",)),
                 T4Stub(sym("UnitSetNextOrder"), log_regs=("eax", "edx")),
                 T4Stub(sym("PaletteCycleEnable"), log_regs=())]
        go("OrderUpdateJoin_", "order_update_join_reference.c", 0x14084, cases, stubs, glob)


def test_order_update_spell():
    op = sym("order_props")
    so = sym("spell_order")
    glob = [(so, 2)]
    for r2 in (0, 1):
        stubs = [T4Stub(0x1de60, ret=5, log_regs=("eax", "edx")),
                 T4Stub(0x1def0, ret=3, log_regs=("eax",)),
                 T4Stub(sym("SpellCastOrder"), log_regs=("eax",)),
                 T4Stub(0x2eefc, ret=r2, log_regs=("eax", "edx", "ebx"))]
        cases = []
        for p in (0, 1, 2, 3, 4, 5, 6, 7):
            for dest in (None, {}):
                cases.append(C("p%d_%s" % (p, dest is None),
                               {0x1f: (3, 1), 0x08: (1, 1), 0x0a: (0x11223344, 4), 0x4e: (0x55667788, 4)},
                               d=dest, g={op + 3: bytes([p])}))
        go("OrderUpdateSpell_", "order_update_spell_reference.c", 0x14140, cases, stubs, glob)


def test_order_update_repair():
    mh = sym("unit_max_hp")
    glob = [(0x50060, 20), (0x50074, 20)]
    res_ok = {0x50060: struct.pack("<5I", 5, 5, 5, 5, 5), 0x50074: struct.pack("<5I", 5, 5, 5, 5, 5)}
    res_no = {0x50060: struct.pack("<5I", 0, 5, 5, 5, 5), 0x50074: struct.pack("<5I", 5, 5, 5, 5, 5)}
    res_no2 = {0x50060: struct.pack("<5I", 5, 5, 5, 5, 5), 0x50074: struct.pack("<5I", 0, 5, 5, 5, 5)}

    def g(res):
        r = dict(res)
        r[mh + 10] = struct.pack("<H", 100)
        return r
    ut = {0x1f: (1, 1), 0x1e: (0, 1), 0x1b: (5, 1)}
    cases = [
        C("full", ut, {0x10: (0x80, 2), 0x16: (100, 2), 0x1b: (5, 1)}, g(res_ok)),
        C("heal", ut, {0x10: (0x80, 2), 0x16: (50, 2), 0x1b: (5, 1)}, g(res_ok)),
        C("heal_cap", ut, {0x10: (0x80, 2), 0x16: (96, 2), 0x1b: (5, 1)}, g(res_ok)),
        C("heal_cnt", ut, {0x10: (0x80, 2), 0x16: (50, 2), 0x1b: (5, 1), 0x50: (0x20000, 4)}, g(res_ok)),
        C("nores0", ut, {0x10: (0x80, 2), 0x16: (50, 2), 0x1b: (5, 1)}, g(res_no)),
        C("nores0b", ut, {0x10: (0x80, 2), 0x16: (50, 2), 0x1b: (5, 1)}, g(res_no2)),
        C("nores1", {0x1f: (1, 1), 0x1e: (1, 1), 0x1b: (5, 1)}, {0x10: (0x80, 2), 0x16: (50, 2), 0x1b: (5, 1)}, g(res_no)),
        C("alt4e", ut, {0x10: (0, 2), 0x4e: (1, 1), 0x16: (50, 2), 0x1b: (5, 1)}, g(res_ok)),
        C("idle", ut, {0x10: (0, 2), 0x16: (50, 2), 0x1b: (5, 1)}, g(res_ok)),
    ]
    for r1 in (0, 1):
        for r2 in (0, 1):
            stubs = [T4Stub(sym("UnitRetaliate"), ret=r1, log_regs=("eax",)),
                     T4Stub(0x2eefc, ret=r2, log_regs=("eax", "edx", "ebx")),
                     T4Stub(0x210dc, log_regs=("eax",)), T4Stub(0x1cd50, log_regs=("eax",)),
                     T4Stub(0x1def0, ret=2, log_regs=("eax",)),
                     T4Stub(sym("UnitSetNextOrder"), log_regs=("eax", "edx")),
                     T4Stub(0x19f70, log_regs=("eax", "edx"))]
            go("OrderUpdateRepair_", "order_update_repair_reference.c", 0x141e0, cases, stubs, glob)


def test_unit_work_progress():
    cf = sym("cheat_flags")
    sd = sym("status_dirty")
    glob = [(cf, 4), (sd, 2)]

    def mk(label, fl, cnt, a, b, cheat=0):
        return C(label, {0x0e: (fl, 2), 0x3f: (cnt, 1), 0x40: (a, 1), 0x41: (b, 1)},
                 g={cf: struct.pack("<I", cheat), sd: b"\x00\x00"}, extra=(7,))
    cases = [mk("dirty", 0x30, 3, 1, 4), mk("tick", 0, 3, 1, 4), mk("exp", 0, 1, 1, 4),
             mk("done", 0, 1, 5, 4), mk("eq", 0, 1, 4, 4), mk("cheat", 0, 5, 2, 4, 2),
             mk("cheatdone", 0, 5, 9, 4, 2)]
    for r in (0, 1):
        stubs = [T4Stub(sym("UnitRetaliate"), ret=r, log_regs=("eax",)),
                 T4Stub(sym("UnitSetNextOrder"), log_regs=("eax", "edx"))]
        go("UnitWorkProgress_", "unit_work_progress_reference.c", 0x14334, cases, stubs, glob)


def test_order_update_produce():
    sv = sym("score_value")
    lc = sym("unit_lumber_cost")
    tc = sym("training_count")
    mf = sym("map_flags")
    glob = [(0x50060, 20), (0x50074, 20), (tc, 10), (sv, 0x40), (lc, 0x40)]
    base = {0x1e: (1, 1), 0x1b: (2, 1), 0x08: (0, 4), 0x42: (3, 2), 0x44: (4, 2),
            0x0a: (0x00050000, 4), 0x0c: (6, 2)}

    def post(emu):
        emu.write(ST['m'], b"\xff" * 8192)
        emu.write(mf, struct.pack("<I", ST['m']))
    g = {0x50060: struct.pack("<5I", 1, 2, 3, 4, 5), 0x50074: struct.pack("<5I", 5, 4, 3, 2, 1),
         tc: struct.pack("<5H", 3, 3, 3, 3, 3), sv + 5: b"\x64", lc + 5: b"\x28",
         sv + 0x35: b"\x10", lc + 0x35: b"\x10"}

    def mk(label, fl, ot, ow):
        return C(label, {**base, 0x0e: (fl, 2), 0x3e: (ot, 1), 0x1e: (ow, 1)}, g=g, post=post)
    cases = [mk("cancel5", 0x20, 5, 1), mk("cancel35", 0x20, 0x35, 1), mk("wall", 0, 0x35, 1),
             mk("ok_o0", 0, 5, 0), mk("ok_o1", 0, 5, 1)]
    for r in (0, 1):
        for r2 in (0, 1):
            stubs = [T4Stub(0x14334, ret=r, log_regs=("eax", "edx")),
                     T4Stub(0x19f70, log_regs=("eax", "edx")),
                     T4Stub(sym("SndTrainingComplete"), log_regs=("eax",)),
                     T4Stub(0x20d74, log_regs=("eax", "edx", "ebx")),
                     T4Stub(sym("TerrainApplyCellFlags"), log_regs=("eax", "edx", "ebx")),
                     T4Stub(0x2e650, ret=r2, log_regs=("eax", "edx", "ebx", "ecx"), stack_pop=4)]
            go("OrderUpdateProduce_", "order_update_produce_reference.c", 0x143cc, cases, stubs, glob)


def test_dispatch_fatal():
    go("DispatchFatal_", "dispatch_fatal_reference.c", 0x145d0, [C("a")],
       [T4Stub(0x30bf0, log_regs=())])
