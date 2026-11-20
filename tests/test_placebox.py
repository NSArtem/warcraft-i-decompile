import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.emu import Emu
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/placebox')
NEP = 0x5a11a
PTYPE = 0x59bd0
PACT = 0x59bd2
OPROPS = 0x534f4
OMASK = 0x51dca
MAPFLAGS = 0x5857c


def _buf(size=0x100):
    return Emu().alloc(size, 16)


def w16(v):
    return struct.pack("<H", v & 0xFFFF)


def w32(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


def pt(x, y):
    return (y << 16) | x


def test_t3_files_still_match():
    t4spec.assert_t3_matches(path('src/placebox'), ['order_update_move.c', 'place_box_active.c', 'place_box_cancel.c', 'place_box_shutdown.c', 'unit_is_passable.c'])


def test_reference_files_still_mismatch():
    t4spec.assert_ref_mismatch(path('src/placebox'), ['place_box_confirm_reference.c', 'place_box_create_building_reference.c', 'place_box_init_reference.c', 'place_box_road_reference.c', 'place_box_wall_reference.c', 'unit_order_target_finish_reference.c'])


def test_unit_order_target_finish():
    for r2207 in (0, 1):
        for r2220 in (0, 1):
            cases, watch = [], [(OPROPS, 0x80)]

            def init(e, r2207=r2207, r2220=r2220):
                u = e.alloc(0x100, 16)
                watch.append((u, 0x100))
                for cur in (0x12, 0x05, 0x1f, 0x03):
                    for nxt in (0x1f, 0x07):
                        for props in (0, 2):
                            def setup(em, u=u, cur=cur, nxt=nxt, props=props):
                                em.write(u, b"\x00" * 0x100)
                                em.write(u + 0x0f, b"\xff")
                                em.write(u + 0x20, bytes([nxt]))
                                em.write(u + 0x21, bytes([cur]))
                                em.write(OPROPS + cur, bytes([props]))
                            cases.append(T4Case(args=(u,), setup=setup,
                                                label=f"c{cur:x}n{nxt:x}a{r2207}b{r2220}p{props}"))

            t4spec.run_spec(
                os.path.join(SRC, 'unit_order_target_finish_reference.c'),
                'UnitOrderTargetFinish_', 0x22464, cases,
                watch=watch, init_emu=init,
                stubs=[T4Stub(0x2cebc, log_regs=("eax",)),
                       T4Stub(0x223bc, log_regs=("eax",)),
                       T4Stub(0x2207c, ret=r2207, log_regs=("eax",)),
                       T4Stub(0x2220c, ret=r2220, log_regs=("eax", "edx")),
                       T4Stub(0x2eeac, log_regs=("eax", "edx"))],
                out_regs=())


def test_place_box_init():
    t4spec.run_spec(
        os.path.join(SRC, 'place_box_init_reference.c'),
        'PlaceBoxInit_', 0x224e0,
        [T4Case(args=(), mem={PACT: b"\x01\x01"}, label="active")],
        watch=[(0x5ac0a, 0x12), (0x52b24, 0x10), (PACT, 2)],
        stubs=[T4Stub(0x32558, ret=0x123450, log_regs=("eax",))],
        out_regs=())


def test_place_box_create_building():
    for ret in (0, 0x4000):
        cases = []

        def init(e):
            worker = e.alloc(0x100, 16)
            for nep in (0, 1):
                for x, y in ((0, 0), (5, 9), (63, 2)):
                    cases.append(T4Case(args=(worker, pt(x, y)),
                                        mem={NEP: w16(nep), PTYPE: bytes([0x10, 0x20])},
                                        label=f"nep{nep}_{x}_{y}"))

        t4spec.run_spec(
            os.path.join(SRC, 'place_box_create_building_reference.c'),
            'PlaceBoxCreateBuilding_', 0x229c8, cases,
            init_emu=init,
            stubs=[T4Stub(0x2e6f4, ret=ret, log_regs=("eax", "edx", "ebx")),
                   T4Stub(0x19f70, log_regs=("eax", "edx")),
                   T4Stub(0x1b9b8, log_regs=()),
                   T4Stub(0x2e100, log_regs=("eax", "edx", "ebx", "ecx"), stack_pop=4)])


def test_place_box_road():
    cases = [T4Case(args=(pt(x, y),),
                    mem={NEP: w16(nep), OMASK: w16(0x1234) + w16(0x4321)},
                    label=f"nep{nep}_{x}_{y}")
             for nep in (0, 1) for x, y in ((0, 0), (7, 3), (63, 63))]
    t4spec.run_spec(
        os.path.join(SRC, 'place_box_road_reference.c'),
        'PlaceBoxRoad_', 0x22a4c, cases,
        stubs=[T4Stub(0x2c100, log_regs=("eax", "edx", "ebx")),
               T4Stub(0x1bd54, log_regs=())])


def test_place_box_wall():
    cases, watch = [], []
    holder = [0]

    def init(e):
        worker = e.alloc(0x100, 16)
        holder[0] = worker
        watch.append((worker, 0x100))
        for nep in (0, 1):
            for x, y in ((0, 0), (7, 3), (63, 63)):
                cases.append(T4Case(args=(worker, pt(x, y)), mem={NEP: w16(nep)},
                                    label=f"nep{nep}_{x}_{y}"))

    t4spec.run_spec(
        os.path.join(SRC, 'place_box_wall_reference.c'),
        'PlaceBoxWall_', 0x22a98, cases,
        watch=watch, init_emu=init,
        stubs=[T4Stub(0x1bd54, log_regs=()),
               T4Stub(0x2c268, log_regs=("eax", "edx")),
               T4Stub(0x25cc4, fn=lambda e, log: (log(e.reg("eax")), holder[0])[1]),
               T4Stub(0x115f4, log_regs=("eax", "edx"))])


def test_place_box_confirm():
    for chk in (0, 3):
        for cret in (0, 1):
            for r20d74 in (0, 1):
                cases, watch = [], []
                holder = [0]

                def init(e):
                    u = e.alloc(0x100, 16)
                    flags = e.alloc(0x2000, 16)
                    holder[0] = u
                    watch.append((flags, 0x2000))
                    for nep in (0, 1):
                        for ptype in (0x10, 0x34, 0x35):
                            for utype in (0, 2):
                                def setup(em, u=u, flags=flags, utype=utype):
                                    em.write(u, b"\x00" * 0x100)
                                    em.write(u + 0x1b, bytes([utype]))
                                    em.write(u + 8, w16(0) + w16(3) + w16(0) + w16(2))
                                    em.write(MAPFLAGS, w32(flags))
                                    em.write(flags, bytes([0x00, 0xff]) * 0x1000)
                                cases.append(T4Case(
                                    args=(pt(4, 5),),
                                    mem={NEP: w16(nep), PTYPE: bytes([ptype, ptype])},
                                    setup=setup, label=f"n{nep}t{ptype:x}u{utype}"))

                t4spec.run_spec(
                    os.path.join(SRC, 'place_box_confirm_reference.c'),
                    'PlaceBoxConfirm_', 0x22ae4, cases,
                    watch=watch, init_emu=init,
                    stubs=[T4Stub(0x2256c, ret=chk, log_regs=("eax", "edx")),
                           T4Stub(0x19f70, log_regs=("eax", "edx")),
                           T4Stub(0x22930, log_regs=()),
                           T4Stub(0x25cc4, fn=lambda e, log: (log(), holder[0])[1]),
                           T4Stub(0x229c8, ret=cret, log_regs=("eax", "edx")),
                           T4Stub(0x22a4c, ret=cret, log_regs=("eax",)),
                           T4Stub(0x22a98, ret=cret, log_regs=("eax", "edx")),
                           T4Stub(0x20d74, ret=r20d74, log_regs=("eax", "edx", "ebx")),
                           T4Stub(0x22798, log_regs=("eax",))],
                    out_regs=())
