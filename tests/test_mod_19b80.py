import os
import struct

import pytest

from wc1 import t4spec
from wc1 import path
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = "src/mod_19b80/"

D_HELP_TIMER = 0x5951c
D_AUX_TIMER = 0x5951e
D_PENDING = 0x59508
D_AUX_FLAG = 0x5ab7a
D_DEMO = 0x5152c


def w16(v):
    return struct.pack("<H", v & 0xFFFF)


def w32(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_19b80'), ['game_screen_input_reset.c', 'map_view_recall.c', 'map_view_save.c', 'status_bar_bitmap_release.c', 'status_help_text_set.c', 'ui_press_dispatch.c', 'ui_release_dispatch.c'])


def test_reference_near_miss():
    t4spec.assert_ref_mismatch(path('src/mod_19b80'), ['game_hotkey_dispatch_reference.c', 'game_screen_mouse_update_reference.c', 'map_view_bookmarks_init_reference.c', 'status_help_timers_tick_reference.c'])


def test_map_view_bookmarks_init():
    watch = []
    state = {}

    def init_emu(emu):
        units = emu.alloc(0x5c * 200 + 16, 16)
        hall = emu.alloc(16, 16)
        state["units"] = units
        state["hall"] = hall
        watch[:] = [(0x50e3e, 12), (D_HELP_TIMER, 4), (D_PENDING, 4),
                    (0x51804, 4), (0x5ab7c, 16), (0x59500, 4), (hall, 16)]

    def mk(hall_set, which, pos):
        def setup(emu):
            units = state["units"]
            hall = state["hall"]
            emu.write(units, b"\x00" * (0x5c * 200 + 16))
            emu.write(hall, struct.pack("<HHHH", 0, 0, 0, 0))
            for i in range(200):
                emu.write(units + i * 0x5c + 0x1e, b"\x01")
            if which is not None:
                emu.write(units + which * 0x5c + 0x1e, b"\x00")
                emu.write(units + which * 0x5c + 10, struct.pack("<hh", *pos))
            emu.write(0x59640, w32(units))
            if hall_set:
                emu.write(hall, struct.pack("<hh", *pos))
                emu.write(0x58db0, w32(hall))
            else:
                emu.write(0x58db0, w32(0))
        return setup

    cases = []
    for hs in (0, 1):
        for pos in ((0, 0), (3, 2), (20, 30), (63, 63), (10, 70), (100, 4), (7, 5)):
            cases.append(T4Case(setup=mk(hs, 5, pos), label=f"hs{hs}{pos}"))
    cases.append(T4Case(setup=mk(0, None, (0, 0)), label="none"))
    t4spec.run_spec(SRC + "map_view_bookmarks_init_reference.c", "MapViewBookmarksInit_", 0x19db4,
                    cases, watch=watch, init_emu=init_emu, out_regs=(),
                    stubs=(T4Stub(0x32558, ret=0x123450, log_regs=("eax",)),))


def test_status_help_timers_tick():
    def mk(a, b, p, f):
        def setup(emu):
            emu.write(D_HELP_TIMER, w16(a))
            emu.write(D_AUX_TIMER, w16(b))
            emu.write(D_PENDING, w32(p))
            emu.write(D_AUX_FLAG, w16(f))
        return setup
    cases = [T4Case(setup=mk(a, b, 0x1234, 0x77), label=f"{a},{b}")
             for a in (0, 1, 2, 0xffff) for b in (0, 1, 2, 0xffff)]
    t4spec.run_spec(SRC + "status_help_timers_tick_reference.c", "StatusHelpTimersTick_", 0x19f94,
                    cases, watch=[(D_HELP_TIMER, 4), (D_PENDING, 4), (D_AUX_FLAG, 2)], out_regs=())


def test_game_hotkey_dispatch():
    watch = []
    state = {}

    def init_emu(emu):
        state["evt"] = 0x59540
        watch[:] = [(state["evt"], 32)]

    def mk(key, demo=0):
        def setup(emu):
            emu.write(state["evt"], b"\x00" * 8 + w16(key) + b"\x00" * 22)
            emu.write(D_DEMO, w16(demo))
        return setup

    keys = [0x42d, 0xd, 0x10d, 0xc, 0x20c, 0x418, 0x57, 0x58, 0x3b, 0x423, 0x2e,
            0x3f, 0x40, 0x42, 0x43, 0x3c, 0x3d, 0x3e, 0x13c, 0x23d, 0x33e, 0x39, 0x41, 0x1, 0x3e
            ]
    cases = [T4Case(setup=mk(k), label=f"k{k:x}") for k in keys]
    cases.append(T4Case(setup=mk(0x42d, 1), label="demo"))

    def sub_evt(e, log):
        log(e.reg("eax") - state["evt"])
        return state.get("ret", 0)

    def callee(addr, ret=0):
        return T4Stub(addr, ret=ret, log_regs=("eax",))

    for r1690 in (0, 1):
        for r29354 in (0, 1):
            def init2(emu, r1690=r1690, r29354=r29354):
                init_emu(emu)
            stubs = (T4Stub(0x1b690, ret=r1690, log_regs=("edx",)),
                     callee(0x1b5d0), callee(0x25cc4, 0x5555),
                     callee(0x257f8), callee(0x29354, r29354),
                     callee(0x32a80), callee(0x21c20),
                     callee(0x19d68), callee(0x19d8c))
            w = []

            def ie(emu, init2=init2, w=w):
                init2(emu)
                w[:] = list(watch)

            def mk_case(c, ):
                def setup(emu):
                    c.setup(emu)
                return setup
            cs = []
            for c in cases:
                cs.append(T4Case(args=(0,), setup=c.setup, label=c.label))

            def fix(emu):
                pass
            cs2 = []
            for c in cs:
                cs2.append(c)
            # args must be evt pointer: set via regs_in lazily
            for c in cs2:
                c.args = ()
                c.regs_in = None
            t4spec.run_spec(SRC + "game_hotkey_dispatch_reference.c", "GameHotkeyDispatch_", 0x19fd8,
                            _with_evt(cs2, state), watch=w, init_emu=ie, out_regs=(), stubs=stubs)


class _EvtArg(int):
    pass


def _with_evt(cases, state):
    out = []
    for c in cases:
        def setup(emu, c=c):
            c.setup(emu)
        out.append(T4Case(args=(_LazyEvt(state),), setup=setup, label=c.label))
    return out


class _LazyEvt(int):
    def __new__(cls, state):
        # evt buffer is allocated deterministically in init_emu; resolved at use
        return int.__new__(cls, 0x59540)


def test_game_screen_mouse_update():
    watch = [(0x59504, 0x20), (0x5a7c9, 1), (D_HELP_TIMER, 4)]
    RECTS = {
        0x53514: 0x04, 0x53516: 0x48, 0x53518: 0x3f, 0x5351a: 0xc7,
        0x599ec: 0x40, 0x599ee: 0xc8, 0x599f0: 0x00, 0x599f2: 0x00,
        0x51eec: 0x0c, 0x51eee: 0x37, 0x51ef0: 0xbb, 0x51ef2: 0xf0,
    }

    def mk(mx, my, locked=0, tmr=0, flag=0, a=0, b=0, side=(0x40, 0x10, 0x60, 0x30)):
        def setup(emu):
            emu.write(0x53514, struct.pack("<hhhh", 4, 0x48, 0x3f, 0xc7))
            emu.write(0x599ec, struct.pack("<hhhh", *side))
            emu.write(0x51eec, struct.pack("<hhhh", 0xc, 0x37, 0xbb, 0xf0))
            emu.write(0x59428, struct.pack("<hh", mx, my))
            emu.write(0x59650, w16(locked))
            emu.write(0x5a918, w16(flag))
            emu.write(D_HELP_TIMER, w16(tmr))
            emu.write(0x59500, w32(0x1111))
            emu.write(D_PENDING, w32(0x2222))
            emu.write(0x5a420, w16(7))
            emu.write(0x5a90e, w16(a))
            emu.write(0x5a9b6, w16(b))
            emu.write(0x5a7c9, b"\x01")
            emu.write(0x59510, w32(0x3000))
            emu.write(0x59514, w32(0x3100))
            emu.write(0x59518, w32(0x3200))
        return setup

    pts = [(10, 100), (4, 0x48), (0x3f, 0xc7), (0x41, 0x20), (0x50, 0x20), (0x30, 0x10),
           (100, 100), (200, 100), (0x0c, 0x37), (0xbb, 0xf0), (1000, 1000), (-5, 5)]
    cases = []
    for p in pts:
        for locked in (0, 1):
            cases.append(T4Case(setup=mk(p[0], p[1], locked, flag=1), label=f"{p}L{locked}"))
        cases.append(T4Case(setup=mk(p[0], p[1], 0, tmr=5), label=f"{p}t"))
        cases.append(T4Case(setup=mk(p[0], p[1], 0, a=1), label=f"{p}a"))
        cases.append(T4Case(setup=mk(p[0], p[1], 0, b=1), label=f"{p}b"))
    for r2b308 in (0, 1):
        for rpb in (0, 1):
            stubs = (T4Stub(0x13dd0, log_regs=("eax",)),
                     T4Stub(0x22538, ret=rpb, log_regs=()),
                     T4Stub(0x25aa4, ret=3, log_regs=("eax",)),
                     T4Stub(0x25b4c, ret=4, log_regs=()),
                     T4Stub(0x28e88, log_regs=("eax", "edx")),
                     T4Stub(0x2b308, ret=r2b308, log_regs=()),
                     T4Stub(0x2b67c, log_regs=("eax", "edx")))
            t4spec.run_spec(SRC + "game_screen_mouse_update_reference.c", "GameScreenMouseUpdate_", 0x1a168,
                            cases, watch=watch, out_regs=(), stubs=stubs)
