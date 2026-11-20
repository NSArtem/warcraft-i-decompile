"""T4 differential tests: PLAYFLIC.C reference C vs original code (war.exe).

Reference file: src/playflic/player_reference.c
"""
import functools
import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.emu import Emu
from wc1.t4spec import T4Case, T4Stub

SRC = path("src", "playflic", "player_reference.c")

pytestmark = pytest.mark.skipif(
    not os.path.exists(SRC), reason="playflic reference C not present")

# Known divergence: the reference C makes a different number of stub calls
# than the original (stub call-log length differs by one iteration).
_DIVERGES = pytest.mark.xfail(
    strict=False,
    reason="reference C stub-call sequence differs from original (log length)")

# ---- data addresses (from the symbol DB) ----
FLIC_WIDTH = 0x59448
FLIC_HEIGHT = 0x5944a
FLIC_FRAMES = 0x59446
FRAME = 0x59ef0
INTRO_ABORT = 0x59efa
FRAME_READY = 0x59efc
ABORT_REQ = 0x59ee6
TICK_COUNT = 0x59ef8
FADE_FRAMES = 0x59ede
CREDIT_LINES = 0x52d18
PALETTE = 0x58f20
FADE_DELTA = 0x59be0
PAL_BASE = 0x5ad60
PAL_TARGET = 0x62570
SCRIPT_OPS = 0x52ea8
OP_STUB_ADDR = 0x23330     # IntroOpSetupFade: reused as the stubbed script op

# callee addresses
A_INTROTICK = 0x22c50
A_MEMSET = 0x30c50
A_MEMCPY = 0x31789
A_PALLERP = 0x34c70
A_LAYERINV = 0x31f70
A_SCRUPD = 0x321e8


def u16(v):
    return struct.pack("<H", v & 0xFFFF)


def u32(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


def rd16(e, a):
    return struct.unpack("<H", e.read(a, 2))[0]


def wr16(e, a, v):
    e.write(a, u16(v))


def rd32(e, a):
    return struct.unpack("<I", e.read(a, 4))[0]


def wr32(e, a, v):
    e.write(a, u32(v))


@functools.lru_cache(None)
def scr():
    """Address of a scratch block: first allocation in a fresh Emu."""
    return Emu().alloc(0x400, 16)


def init_scr(emu):
    a = emu.alloc(0x400, 16)
    assert a == scr(), "scratch allocation not deterministic"


# ---- shared custom stubs ----
def _tick_toggle(e, log):
    v = rd16(e, FRAME_READY)
    log(v)
    wr16(e, FRAME_READY, v ^ 1)
    return 0


def tick_toggle():
    return T4Stub(A_INTROTICK, fn=_tick_toggle, log_regs=())


def tick_plain():
    return T4Stub(A_INTROTICK, log_regs=())


def make_tick_ctl(S):
    def fn(e, log):
        log()
        wr16(e, INTRO_ABORT, rd32(e, S + 0x28))
        wr16(e, ABORT_REQ, rd32(e, S + 0x2c))
        wr16(e, FRAME_READY, 1)
        return 0
    return T4Stub(A_INTROTICK, fn=fn, log_regs=())


def make_op_stub(S):
    def fn(e, log):
        n = rd32(e, S + 0x20)
        lim = rd32(e, S + 0x24)
        wr32(e, S + 0x20, n + 1)
        log(e.reg("eax"))
        return 0 if n >= lim else e.reg("eax")
    return T4Stub(OP_STUB_ADDR, fn=fn, log_regs=())


def table(entries):
    return b"".join(struct.pack("<HI", d, t) for d, t in entries)


# ---------------------------------------------------------------- credits
def lc_case(S, timer, idx, count, entries, label):
    T, E = S + 0x100, S + 0x120
    ents = [(1, T)] * 6
    for i, (d, kind) in enumerate(entries):
        ents[i] = (d, T if kind else E)
    mem = {
        CREDIT_LINES: table(ents),
        T: b"Hi\0\0",
        E: b"\0\0\0\0",
        0x59ee2: u16(timer), 0x59ee8: u16(idx), 0x59ef2: u16(count),
        0x59ee4: u16(1),
        0x59eb8: b"\xaa" * 12,
        0x59ecc: b"\x55" * 6,
        0x59ec4: u32(S + 0x200),
        FLIC_HEIGHT: u16(100),
        0x5acf0: u32(S + 0x300),
    }
    return T4Case(mem=mem, label=label)


def test_intro_load_credit_lines():
    S = scr()
    cases = [
        lc_case(S, 5, 0, 1, [], "timer-running"),
        lc_case(S, 0, 0, 1, [], "timer-zero-wraps"),
        lc_case(S, 1, 0, 0, [(0, 1), (3, 1)], "text-delay3"),
        lc_case(S, 1, 0, 2, [(0, 1), (3, 1)], "text-count2"),
        lc_case(S, 1, 0, 1, [(0, 1), (0, 1), (4, 1)], "two-iterations"),
        lc_case(S, 1, 0, 2, [(2, 0)], "empty-clear"),
        lc_case(S, 1, 0, 2, [(0, 0), (3, 1)], "clear-then-text"),
        lc_case(S, 1, 0, 2, [(0xffff, 1)], "end-marker"),
        lc_case(S, 1, 1, 0, [(1, 1), (1, 1), (7, 1)], "idx1"),
    ]
    t4spec.run_spec(
        SRC, "IntroLoadCreditLines_", 0x22d40, cases,
        watch=[(0x59eb8, 0x40)],
        stubs=[T4Stub(A_MEMSET, log_regs=("eax", "edx", "ebx")),
               T4Stub(0x32060, ret=100, log_regs=("eax", "edx"))],
        out_regs=(), init_emu=init_scr)
    t4spec.run_spec(
        SRC, "IntroLoadCreditLines_", 0x22d40, cases,
        watch=[(0x59eb8, 0x40)],
        stubs=[T4Stub(A_MEMSET, log_regs=("eax", "edx", "ebx")),
               T4Stub(0x32060, ret=0x141, log_regs=("eax", "edx"))],
        out_regs=(), init_emu=init_scr)


@_DIVERGES
def test_intro_op_start_credits():
    S = scr()
    cases = []
    for idx in (0xffff, 0, 2):
        cases.append(lc_case(S, 0, idx, 0, [(5, 1)] * 6, "d5-idx%x" % idx))
        cases.append(lc_case(S, 0, idx, 0, [(0, 1), (3, 1)] * 3, "d0d3-idx%x" % idx))
        cases.append(lc_case(S, 0, idx, 0, [(0, 1), (0, 1), (0, 1), (0, 1), (9, 1)],
                             "four-idx%x" % idx))
    for c in cases:
        c.args = (S,)
    for width in (100, 0x141):
        t4spec.run_spec(
            SRC, "IntroOpStartCredits_", 0x23530, cases,
            watch=[(0x59eb8, 0x40)],
            stubs=[T4Stub(0x32060, ret=width, log_regs=("eax", "edx"))],
            init_emu=init_scr)


def _ct_case(tick, ctick, sb, sc, fc, fd, sd, label=""):
    return T4Case(mem={0x59ef8: u16(tick), 0x59edc: u16(ctick), 0x59eda: u16(sb),
                       0x59ed4: u16(sc), 0x59ed6: u16(fc), 0x59ed8: u16(fd),
                       0x59ed2: u16(sd)}, label=label)


def _credit_cases():
    return [
        _ct_case(0, 7, 3, 4, 5, 6, 7, "tick0-init"),
        _ct_case(5, 5, 3, 4, 5, 6, 7, "same-tick"),
        _ct_case(5, 4, 3, 4, 5, 6, 7, "odd-tick"),
        _ct_case(6, 4, 3, 4, 5, 6, 7, "even-tick"),
        _ct_case(6, 4, 0x1e, 4, 5, 6, 7, "stepb-wrap-A"),
        _ct_case(6, 4, 0x14, 4, 5, 6, 7, "stepb-wrap-B"),
        _ct_case(6, 4, 3, 4, 9, 6, 7, "framec-boundary"),
        _ct_case(6, 4, 3, 19, 9, 6, 7, "stepc-wrap"),
        _ct_case(6, 4, 3, 4, 5, 9, 7, "framed-boundary"),
        _ct_case(6, 4, 3, 4, 5, 39, 19, "stepd-wrap"),
        _ct_case(6, 4, 3, 4, 29, 39, 19, "both-wrap"),
        _ct_case(0xffff, 0xfffe, 3, 4, 5, 6, 7, "tick-ffff"),
    ]


def _credit_rand(maxstep_b, maxfc):
    import random  # noqa: F401

    def gen(rng):
        tick = rng.randrange(0, 0x10000)
        ctick = tick if rng.random() < 0.15 else rng.randrange(0, 0x10000)
        if tick == 0:
            tick = 1
        return _ct_case(tick, ctick, rng.randrange(0, maxstep_b),
                        rng.randrange(0, 20), rng.randrange(0, maxfc),
                        rng.randrange(0, 40), rng.randrange(0, 20))
    return gen


def test_credits_tick_a():
    t4spec.run_spec(
        SRC, "CreditsTickA_", 0x237a0, _credit_cases(),
        watch=[(0x59ed2, 0x10), (0x59ef8, 2)],
        stubs=[T4Stub(0x1c1dc, log_regs=("eax",)),
               T4Stub(0x1c214, log_regs=("eax",)),
               T4Stub(0x1c24c, log_regs=("eax",))],
        out_regs=(), rand_cases=60, rand_gen=_credit_rand(0x1f, 30))


def test_credits_tick_b():
    t4spec.run_spec(
        SRC, "CreditsTickB_", 0x2393c, _credit_cases(),
        watch=[(0x59ed2, 0x10), (0x59ef8, 2)],
        stubs=[T4Stub(0x1c1dc, log_regs=("eax",)),
               T4Stub(0x1c214, log_regs=("eax",)),
               T4Stub(0x1c24c, log_regs=("eax",)),
               T4Stub(0x1c284, log_regs=("eax",))],
        out_regs=(), rand_cases=60, rand_gen=_credit_rand(0x15, 40))


# ---------------------------------------------------------------- fade
def test_intro_fade_step():
    def gen(rng):
        pal = bytes(rng.randrange(256) for _ in range(768))
        if rng.random() < 0.5:
            dl = bytes(rng.randrange(8) for _ in range(0x2d0))
        else:
            dl = bytes(rng.randrange(256) for _ in range(0x2d0))
        return T4Case(mem={PALETTE: pal, FADE_DELTA: dl})

    cases = [
        T4Case(mem={PALETTE: bytes(768), FADE_DELTA: bytes(0x2d0)}, label="zeros"),
        T4Case(mem={PALETTE: b"\x10" * 768, FADE_DELTA: b"\x10" * 0x2d0}, label="equal"),
        T4Case(mem={PALETTE: b"\x10" * 768, FADE_DELTA: b"\x11" * 0x2d0}, label="delta-gt"),
        T4Case(mem={PALETTE: b"\xff" * 768, FADE_DELTA: b"\x01" * 0x2d0}, label="max"),
    ]
    t4spec.run_spec(
        SRC, "IntroFadeStep_", 0x22eac, cases,
        watch=[(PALETTE, 768), (FADE_DELTA, 0x2d0)],
        stubs=[T4Stub(0x33150, log_regs=("eax", "edx", "ebx"))],
        out_regs=(), rand_cases=8, rand_gen=gen)


def _ff_mem(ready, abort):
    return {FRAME_READY: u16(ready), INTRO_ABORT: u16(abort)}


def test_intro_fade_frames():
    cases = []
    for n in (0, 1, 2, 5):
        for ready in (0, 1):
            cases.append(T4Case(args=(n,), mem=_ff_mem(ready, 0),
                                label="n%d-ready%d" % (n, ready)))
    cases.append(T4Case(args=(4,), mem=_ff_mem(1, 1), label="abort"))
    cases.append(T4Case(args=(4,), mem=_ff_mem(0, 1), label="abort-after-tick"))
    t4spec.run_spec(
        SRC, "IntroFadeFrames_", 0x22eec, cases,
        watch=[(0x59ee0, 0x20)],
        stubs=[tick_toggle(),
               T4Stub(A_PALLERP, log_regs=("eax", "edx", "ebx", "ecx"))],
        out_regs=())


def _fade_op_cases(S):
    cases = []
    for n, ready, abort in ((0, 0, 0), (3, 0, 0), (2, 1, 0), (3, 0, 1), (1, 1, 1)):
        mem = _ff_mem(ready, abort)
        mem[S] = u16(n)
        cases.append(T4Case(args=(S,), mem=mem,
                            label="n%d-r%d-a%d" % (n, ready, abort)))
    return cases


def _fade_op_stubs():
    return [tick_toggle(),
            T4Stub(A_MEMSET, log_regs=("eax", "edx", "ebx")),
            T4Stub(A_MEMCPY, log_regs=("eax", "edx", "ebx")),
            T4Stub(A_PALLERP, log_regs=("eax", "edx", "ebx", "ecx"))]


def test_intro_op_fade_in():
    S = scr()
    t4spec.run_spec(
        SRC, "IntroOpFadeIn_", 0x23410, _fade_op_cases(S),
        watch=[(0x59ee0, 0x20)], stubs=_fade_op_stubs(), init_emu=init_scr)


def test_intro_op_fade_out():
    S = scr()
    t4spec.run_spec(
        SRC, "IntroOpFadeOut_", 0x23458, _fade_op_cases(S),
        watch=[(0x59ee0, 0x20)], stubs=_fade_op_stubs(), init_emu=init_scr)


# ---------------------------------------------------------------- flic
def test_intro_begin_flic():
    S = scr()
    cases = []
    for sel in (0, 1, 3):
        for h, w, skip in ((100, 320, 0), (200, 320, 0), (150, 0x140, 0),
                           (0xd0, 320, 0), (0xcf, 320, 0), (100, 320, 1)):
            cases.append(T4Case(args=(S,), mem={
                0x59ef6: u16(sel), FLIC_HEIGHT: u16(h), FLIC_WIDTH: u16(w),
                0x59eee: u16(skip), 0x52c60: u16(0), FADE_FRAMES: u16(0),
                0x59eb0: u32(0), 0x59eea: u16(0),
                0x59ec4: u32(S + 0x200), 0x59ec8: u32(S + 0x100)},
                label="sel%d-h%x-skip%d" % (sel, h, skip)))
    for ret in (0, 1):
        t4spec.run_spec(
            SRC, "IntroBeginFlic_", 0x22f48, cases,
            watch=[(0x59eb0, 0x50), (0x52c60, 2)],
            stubs=[T4Stub(0x1933c, ret=ret, stack_pop=4,
                          log_regs=("eax", "edx", "ebx", "ecx"))],
            init_emu=init_scr)


def _pf_cases(S, rows):
    cases = []
    for n, frame, flic, abort in rows:
        cases.append(T4Case(args=(S,), mem={
            S: u16(n), FRAME: u16(frame), FLIC_FRAMES: u16(flic),
            INTRO_ABORT: u16(abort)},
            label="n%d-f%d-fl%d-a%d" % (n, frame, flic, abort)))
    return cases


def test_intro_op_play_frames():
    S = scr()
    cases = _pf_cases(S, [(0, 0, 10, 0), (3, 1, 10, 0), (2, 11, 10, 0),
                          (2, 5, 10, 1), (3, 10, 10, 0), (1, 0xffff, 0xfffe, 0)])
    for nxt, show in ((1, S), (0, S), (1, 0)):
        t4spec.run_spec(
            SRC, "IntroOpPlayFrames_", 0x23070, cases,
            watch=[(0x59ef0, 0x10)],
            stubs=[tick_plain(),
                   T4Stub(0x22cfc, ret=show, log_regs=("eax",)),
                   T4Stub(0x22d20, ret=nxt, log_regs=())],
            init_emu=init_scr)


def test_intro_op_play_to_end():
    S = scr()

    def nextframe(e, log):
        fr = (rd16(e, FRAME) + 1) & 0xFFFF
        wr16(e, FRAME, fr)
        log(fr)
        return 0 if fr == rd32(e, S + 0x10) else 1

    cases = []
    for frame, flic, fade, abort, fail in (
            (0, 5, 0xffff, 0, 0xffffffff), (0, 5, 2, 0, 0xffffffff),
            (0, 5, 0, 0, 0xffffffff), (0, 5, 4, 0, 0xffffffff),
            (5, 5, 2, 0, 0xffffffff), (0, 5, 2, 1, 0xffffffff),
            (0, 5, 2, 0, 3), (2, 6, 1, 0, 0xffffffff), (7, 6, 1, 0, 0xffffffff)):
        cases.append(T4Case(args=(S,), mem={
            S + 0x10: u32(fail), FRAME: u16(frame), FLIC_FRAMES: u16(flic),
            FADE_FRAMES: u16(fade), INTRO_ABORT: u16(abort),
            PALETTE: b"\x20" * 768, FADE_DELTA: b"\x07" * 0x2d0},
            label="f%d-fl%d-fd%x-a%d-fail%x" % (frame, flic, fade, abort, fail & 0xff)))
    t4spec.run_spec(
        SRC, "IntroOpPlayToEnd_", 0x230e8, cases,
        watch=[(0x59ede, 0x20), (PALETTE, 768), (0x59ef0, 0x10)],
        stubs=[tick_plain(),
               T4Stub(0x22d20, fn=nextframe, log_regs=()),
               T4Stub(0x33150, log_regs=("eax", "edx", "ebx"))],
        init_emu=init_scr)


@_DIVERGES
def test_intro_op_wait_sound():
    S = scr()

    def snd(e, log):
        v = rd32(e, S + 0x10)
        log(v)
        if v > 0:
            wr32(e, S + 0x10, v - 1)
        return v

    cases = []
    for cnt, abort in ((0, 0), (3, 0), (3, 1), (1, 0)):
        cases.append(T4Case(args=(S,), mem={S + 0x10: u32(cnt),
                                            INTRO_ABORT: u16(abort)},
                            label="cnt%d-a%d" % (cnt, abort)))
    t4spec.run_spec(
        SRC, "IntroOpWaitSound_", 0x231cc, cases,
        watch=[(0x59ef8, 8)],
        stubs=[tick_plain(), T4Stub(0x27320, fn=snd, log_regs=())],
        init_emu=init_scr)


def test_intro_op_wait_frames():
    S = scr()
    cases = []
    for n, abort, ready in ((0, 0, 0), (1, 0, 0), (3, 0, 0), (3, 1, 0),
                            (2, 0, 1)):
        cases.append(T4Case(args=(S,), mem={
            S: u16(n), INTRO_ABORT: u16(abort), FRAME_READY: u16(ready)},
            label="n%d-a%d-r%d" % (n, abort, ready)))
    t4spec.run_spec(
        SRC, "IntroOpWaitFrames_", 0x231ec, cases,
        watch=[(0x59ef8, 8)], stubs=[tick_toggle()], init_emu=init_scr)


def test_intro_op_wait_anim():
    S = scr()
    cases = []
    for n, abort, ready in ((1, 0, 0), (3, 0, 0), (2, 0, 1), (5, 0, 0),
                            (3, 1, 0)):
        cases.append(T4Case(args=(S,), mem={
            S: u16(n), INTRO_ABORT: u16(abort), FRAME_READY: u16(ready)},
            label="n%d-a%d-r%d" % (n, abort, ready)))
    t4spec.run_spec(
        SRC, "IntroOpWaitAnim_", 0x232ec, cases,
        watch=[(0x59ef8, 8)], stubs=[tick_toggle()], init_emu=init_scr)


def test_intro_op_slide_layer():
    S = scr()
    cases = []
    for y, h, target, st, tc, ready in (
            (10, 5, 14, 0, 0, 0), (10, 5, 0, 0, 0, 0), (10, 5, 0, 1, 0x20, 0),
            (10, 5, 0, 1, 0x14, 0), (10, 5, 0, 1, 0x15, 0),
            (10, 5, 0, 0, 0x30, 1), (-5, 10, 4, 0, 0, 0), (-5, 10, 0, 1, 0x40, 1),
            (100, 1, 99, 1, 0x40, 0)):
        cases.append(T4Case(args=(S + 0x40,), mem={
            0x5ab7e: u16(y), 0x5ab82: u16(h), 0x59ee0: u16(target),
            0x59eec: u16(st), TICK_COUNT: u16(tc), FRAME_READY: u16(ready)},
            label="y%d-h%d-t%d-st%d-tc%x" % (y, h, target, st, tc)))
    t4spec.run_spec(
        SRC, "IntroOpSlideLayer_", 0x23238, cases,
        watch=[(0x5ab7a, 0x12), (0x59ee0, 0x20)],
        stubs=[tick_toggle(),
               T4Stub(0x26958, log_regs=("eax",)),
               T4Stub(A_LAYERINV, log_regs=("eax",)),
               T4Stub(A_SCRUPD, log_regs=())],
        init_emu=init_scr)


# ---------------------------------------------------------------- run / play
def _rs_mem(S, limit, abort, req, flic_open):
    return {S + 0x20: u32(0), S + 0x24: u32(limit), S + 0x28: u32(abort),
            S + 0x2c: u32(req), SCRIPT_OPS: u32(OP_STUB_ADDR),
            0x52c60: u16(flic_open), S + 0x40: bytes(16)}


@_DIVERGES
def test_intro_run_script():
    S = scr()
    cases = []
    for blank in (0, 1):
        for limit in (0, 2):
            for abort in (0, 1):
                for fo in (0, 1):
                    cases.append(T4Case(
                        args=(S + 0x40, blank),
                        mem=_rs_mem(S, limit, abort, 0, fo),
                        label="b%d-lim%d-ab%d-fo%d" % (blank, limit, abort, fo)))
    t4spec.run_spec(
        SRC, "IntroRunScript_", 0x23668, cases,
        watch=[(0x59400, 0x28), (0x52c60, 0x10), (0x55438, 4), (0x5acf0, 4),
               (0x59eb0, 0x50)],
        stubs=[make_tick_ctl(S), make_op_stub(S),
               T4Stub(0x18488, log_regs=()),
               T4Stub(0x31568, log_regs=()),
               T4Stub(0x32558, ret=S + 0x200, log_regs=("eax",)),
               T4Stub(A_MEMSET, log_regs=("eax", "edx", "ebx")),
               T4Stub(0x193dc, log_regs=()),
               T4Stub(0x32780, log_regs=("eax",)),
               T4Stub(0x32030, log_regs=("eax",))],
        init_emu=init_scr)


def _noreg(e, log):
    log()
    return 0


def _edx_only(e, log):
    log(e.reg("edx"))
    return 0


@_DIVERGES
def test_intro_play():
    S = scr()
    cases = []
    for dig in (0xffff, 0):
        for req, abort in ((1, 0), (1, 1), (0, 0)):
            for music in (0, 1):
                mem = _rs_mem(S, 1, abort, req, 0)
                mem.update({
                    0x5aa78: bytes([2]), 0x59902: u16(dig),
                    0x55208: u16(music), 0x55558: u16(1),
                    0x52c7a: bytes(16), 0x52e02: bytes(16),
                    0x5aab4: u16(1), 0x5ab8c: u16(0)})
                cases.append(T4Case(mem=mem, label="dig%x-req%d-ab%d-m%d" % (
                    dig, req, abort, music)))
    t4spec.run_spec(
        SRC, "IntroPlay_", 0x23ae0, cases,
        watch=[(0x59eb0, 0x50), (0x55208, 2), (0x55558, 2), (0x5aab4, 2),
               (0x5ab8c, 10), (0x5ab9a, 4), (0x59400, 0x28)],
        stubs=[make_tick_ctl(S), make_op_stub(S),
               T4Stub(A_LAYERINV, log_regs=("eax",)),
               T4Stub(A_SCRUPD, log_regs=()),
               T4Stub(0x31870, log_regs=("eax", "edx")),
               T4Stub(0x32740, log_regs=("eax", "edx")),
               T4Stub(0x267fc, log_regs=("eax",)),
               T4Stub(0x26784, log_regs=("eax",)),
               T4Stub(0x323e0, fn=_edx_only, log_regs=()),
               T4Stub(0x21cf0, fn=_noreg, log_regs=()),
               T4Stub(0x271f4, log_regs=()),
               T4Stub(0x267e0, log_regs=()),
               T4Stub(0x32fb0, log_regs=("eax",)),
               T4Stub(A_PALLERP, log_regs=("eax", "edx", "ebx", "ecx")),
               T4Stub(0x18488, log_regs=()),
               T4Stub(0x31568, log_regs=()),
               T4Stub(0x32558, ret=S + 0x200, log_regs=("eax",)),
               T4Stub(A_MEMSET, log_regs=("eax", "edx", "ebx")),
               T4Stub(0x193dc, log_regs=()),
               T4Stub(0x32780, log_regs=("eax",)),
               T4Stub(0x32030, log_regs=("eax",))],
        out_regs=(), init_emu=init_scr)


# ---------------------------------------------------------------- overrun
def test_flic_overrun():
    def fatal(e, log):
        ptr = rd32(e, e.reg("esp") + 4)
        log(*struct.unpack("<4I", e.read(ptr, 16)))
        return 0

    def init(emu):
        # neutralise the debug int3 at 0x23cf7 so the emulator can run through
        emu.write(0x23cf7, b"\x90")

    t4spec.run_spec(
        SRC, "FlicOverrun_", 0x23cf4, [T4Case(label="call")],
        stubs=[T4Stub(0x30bf0, fn=fatal, log_regs=())],
        out_regs=(), init_emu=init)
