"""T4 differential tests for mod_16390 reference functions (area mod_16390_c4)."""
import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_16390')
G = {}

LAYERS = 0x5aa90
PALETTE = 0x58f20


def _names():
    out = {}
    for e in t4spec.by_link_lenient().values():
        out[(e["_kind"], e["name"])] = e["addr"]
    return out


def fa(name):
    return _names()[("func", name)]


def da(name):
    return _names()[("data", name)]


def w16(e, addr, v):
    e.write(addr, struct.pack("<H", v & 0xFFFF))


def r16s(e, addr):
    return struct.unpack("<h", e.read(addr, 2))[0]


def sbytes(e, a):
    s = e.cstr(a, 64)
    if isinstance(s, str):
        s = s.encode("latin1")
    return sum(bytearray(s))


def layer_bytes(active, x, y, w, h):
    return struct.pack("<HhhhhII", active, x, y, w, h, 0, 0)


def test_t3_files_still_match():
    t4spec.assert_t3_matches(path('src/mod_16390'), [])


def test_reference_files_still_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_16390'), ['dialog_activate_item_reference.c', 'dialog_run_reference.c', 'outro_play_flic_reference.c'])


# ---------------------------------------------------------------- DialogActivateItem
def _init_act(emu):
    G["d"] = emu.alloc(0x400, 16)
    G["items"] = emu.alloc(0x100, 16)
    G["txt"] = emu.alloc(0x100, 16)
    G["params"] = emu.alloc(0x40, 16)
    G["act_watch"] = [(0x593fa, 2), (0x593f2, 2), (0x55438, 4), (G["txt"], 64)]


def _item(typ, flags=0, code=0, text=0, id_=0):
    return struct.pack("<HHhhHIIIHHH", typ, flags, 0, 0, code, 0, 0, text, id_, 0, 0)


def _act_case(typ, id_=0, code=0, ret=0, label=""):
    def setup(e):
        d = G["d"]
        e.write(d, b"\x00" * 0x400)
        e.write(d + 6, struct.pack("<I", G["params"]))
        e.write(d + 0x26, struct.pack("<I", G["items"]))
        e.write(G["params"], struct.pack("<IIII", fa("DialogDrawItems"), 0, 0, 0))
        e.write(G["txt"], b"abc\x00" + b"\x00" * 60)
        e.write(G["items"], _item(typ, 0, code, 0, id_) + _item(3, 0, 0, G["txt"], 16))
        e.write(d + 0x3f0, struct.pack("<I", ret))
        e.write(0x593fa, struct.pack("<hh", 1, 0)[:2])
        e.write(0x593f2, struct.pack("<h", 0x55))
        e.write(0x55438, struct.pack("<I", 0))

    return T4Case(args=(), regs_in=None, setup=setup, label=label or f"type{typ}_ret{ret}")


def _act_args_setup(case):
    inner = case.setup

    def setup(e):
        inner(e)

    return setup


def _strcpy(e, log):
    dst, src = e.reg("eax"), e.reg("edx")
    s = e.cstr(src, 64)
    if isinstance(s, str):
        s = s.encode("latin1")
    e.write(dst, bytes(s) + b"\x00")
    log(sbytes(e, src))
    return dst


def _editrun(e, log):
    d, item, dest, src = e.reg("eax"), e.reg("edx"), e.reg("ebx"), e.reg("ecx")
    ret = struct.unpack("<I", e.read(G["d"] + 0x3f0, 4))[0]
    log(d, item, sbytes(e, src), ret)
    if ret:
        e.write(dest, b"xyz\x00")
    return ret


def test_dialog_activate_item():
    cases = []
    for typ, id_, code, ret in [(0, 7, 0, 0), (9, 0x12, 0, 0), (1, 0, 0, 0), (2, 0, 0, 0),
                                (6, 0, 0, 0), (7, 0, 0, 0), (7, 0, 0, 1), (10, 0, 0x33, 0),
                                (10, 0, 0x33, 1), (3, 0, 0, 0), (5, 0, 0, 0)]:
        cases.append(_act_case(typ, id_, code, ret))

    # args (d, item) are heap addresses known only after init_emu: patch via regs_in at setup time
    for c in cases:
        inner = c.setup

        def mk(inner):
            def setup(e):
                inner(e)
            return setup
        c.setup = mk(inner)

    def run_case(c):
        return c

    # build per-case arg setters: args are resolved lazily through a wrapper setup that
    # rewrites the registers via regs_in dict mutated in place.
    for c in cases:
        c.regs_in = {}
        inner = c.setup

        def mk2(inner, c):
            def setup(e):
                inner(e)
                c.regs_in["eax"] = G["d"]
                c.regs_in["edx"] = G["items"]
            return setup
        c.setup = mk2(inner, c)

    stubs = [
        T4Stub(fa("DialogEraseText"), log_regs=("eax",)),
        T4Stub(fa("ListSelPrev"), log_regs=("eax", "edx")),
        T4Stub(fa("ListSelNext"), log_regs=("eax", "edx")),
        T4Stub(fa("DialogCallSelect"), log_regs=("eax",)),
        T4Stub(fa("DialogDrawText"), log_regs=("eax",)),
        T4Stub(fa("ListDraw"), log_regs=("eax",)),
        T4Stub(fa("ScreenUpdate"), log_regs=()),
        T4Stub(fa("DialogDrawItems"), log_regs=("eax",)),
        T4Stub(fa("strcpy"), fn=_strcpy),
        T4Stub(fa("EditFieldRun"), fn=_editrun, stack_pop=4),
    ]
    watch = []

    def init_act(emu):
        _init_act(emu)
        watch[:] = G["act_watch"]

    t4spec.run_spec(
        os.path.join(SRC, "dialog_activate_item_reference.c"), "DialogActivateItem_", 0x17ce4,
        cases, stubs=stubs, out_regs=(),
        watch=watch,
        init_emu=init_act)


# ---------------------------------------------------------------- DialogRun
def _init_run(emu):
    G["rd"] = emu.alloc(0x400, 16)


def _run_case(faded, smode, d516, auto, quit_, label):
    def setup(e):
        w16(e, da("palette_faded"), faded)
        w16(e, 0x593f6, smode)
        w16(e, da("dat_516ae"), d516)
        w16(e, 0x51768, auto)
        w16(e, 0x5176a, quit_)
        w16(e, 0x593f2, 0x77)
        w16(e, da("evt_mask"), 0x1234)
        e.write(LAYERS + 22 * 18, layer_bytes(1, 1, 2, 3, 4))
        e.write(LAYERS + 14 * 18, layer_bytes(5, 6, 7, 8, 9))

    return T4Case(args=(0x1234, 5, 6, 3), stack_args=(0x12345678,), setup=setup, label=label)


def _reloc(e, log):
    d = e.reg("eax")
    log(d, *struct.unpack("<HhhI", e.read(d, 10)))


def _load(e, log):
    log(e.reg("eax"))
    return G["rd"]


def test_dialog_run():
    cases = [
        _run_case(0, 0, 0, 0, 0, "plain"),
        _run_case(1, 0, 1, 1, 1, "faded_all"),
        _run_case(0, 1, 1, 1, 0, "mode1"),
        _run_case(1, 0, 0, 0, 1, "faded_quit"),
    ]
    stubs = [
        T4Stub(fa("EvtPump"), log_regs=()),
        T4Stub(fa("TextSetEscapeColors"), log_regs=("eax", "edx")),
        T4Stub(fa("DialogLoad"), fn=_load),
        T4Stub(fa("DialogRelocate"), fn=_reloc),
        T4Stub(fa("DialogCreate"), log_regs=("eax",)),
        T4Stub(fa("SetCursorShape"), log_regs=("eax",)),
        T4Stub(fa("CursorLayerShow"), log_regs=()),
        T4Stub(fa("LayerInvalidate"), log_regs=("eax",)),
        T4Stub(fa("ScreenUpdate"), log_regs=()),
        T4Stub(fa("KeyStateClear"), log_regs=()),
        T4Stub(fa("UiInputInit"), log_regs=()),
        T4Stub(fa("LayerInitFullScreen"), log_regs=("eax",)),
        T4Stub(fa("PaletteFadeIn"), log_regs=("eax",)),
        T4Stub(fa("PaletteFadeOut"), log_regs=("eax",)),
        T4Stub(fa("DialogLoop"), log_regs=("eax",)),
        T4Stub(fa("DialogCallClose"), log_regs=("eax",)),
        T4Stub(fa("DialogFree"), log_regs=("eax",)),
    ]
    t4spec.run_spec(
        os.path.join(SRC, "dialog_run_reference.c"), "DialogRun_", 0x180a8,
        cases, stubs=stubs, out_regs=("eax",),
        watch=[(0x593f0, 2), (0x59400, 40), (0x59410, 4), (0x59414, 4), (0x59420, 4),
               (LAYERS, 32 * 18), (da("evt_mask"), 2)],
        init_emu=_init_run, log_cap=4096)


# ---------------------------------------------------------------- OutroPlayFlic
def _init_outro(emu):
    G["flag"] = emu.alloc(64, 16)
    G["bufs"] = [emu.alloc(64000, 16), emu.alloc(64000, 16)]
    G["n"] = 0


def _outro_case(orc, fo, rw, nf, rs, limit, frames, label):
    def setup(e):
        G["n"] = 0
        e.write(G["flag"], struct.pack("<IIIII", fo, rw, nf, rs, limit))
        w16(e, 0x59432, orc)
        w16(e, 0x50088, 1)
        w16(e, 0x59446, frames)
        w16(e, 0x59434, 0)
        w16(e, 0x59436, 0)
        e.write(LAYERS + 13 * 18, layer_bytes(1, 0, 26 + limit, 10, 5))
        e.write(LAYERS + 14 * 18, layer_bytes(0, 3, 3, 3, 3))

    return T4Case(args=(), setup=setup, label=label)


def _retstub(name, off, regs):
    def f(e, log):
        log(*[e.reg(r) for r in regs])
        return struct.unpack("<I", e.read(G["flag"] + off, 4))[0]

    return T4Stub(fa(name), fn=f, stack_pop=4 if name == "FlicOpen" else 0)


def _alloc(e, log):
    log(e.reg("eax"))
    r = G["bufs"][G["n"] % 2]
    G["n"] += 1
    return r


def _pump(e, log):
    y = r16s(e, LAYERS + 13 * 18 + 4)
    log(y)
    w16(e, 0x59436, 2)
    if y == 29:
        w16(e, 0x59434, 0x14)


def test_outro_play_flic():
    cases = [
        _outro_case(1, 0, 1, 1, 1, 5, 2, "open_fail"),
        _outro_case(1, 1, 0, 1, 1, 5, 2, "rewind_fail"),
        _outro_case(1, 1, 1, 1, 1, 5, 2, "orc_restart"),
        _outro_case(0, 1, 1, 0, 1, 5, 2, "human_nextframe_fail"),
        _outro_case(0, 1, 1, 1, 1, 70, 0x40, "human_long"),
        _outro_case(1, 1, 1, 1, 1, 70, 0x40, "orc_long"),
    ]
    stubs = [
        T4Stub(fa("GdsAlloc"), fn=_alloc),
        T4Stub(fa("GdsFree"), log_regs=("eax",)),
        _retstub("FlicOpen", 0, ("eax", "edx", "ebx", "ecx")),
        _retstub("FlicRewind", 4, ()),
        _retstub("FlicNextFrame", 8, ()),
        _retstub("FlicRestart", 12, ()),
        T4Stub(fa("FlicClose"), log_regs=()),
        T4Stub(fa("LayerInvalidate"), log_regs=("eax",)),
        T4Stub(fa("PaletteSet"), log_regs=("eax", "edx", "ebx")),
        T4Stub(0x1c2bc, log_regs=("eax",)),
        T4Stub(0x1c10c, log_regs=()),
        T4Stub(fa("SndLoadTable"), log_regs=("eax",)),
        T4Stub(fa("MusicStart"), log_regs=("eax",)),
        T4Stub(fa("SndPlayLooped"), log_regs=("eax",)),
        T4Stub(fa("SndPlay"), log_regs=("eax",)),
        T4Stub(fa("SndReleaseAll"), log_regs=()),
        T4Stub(fa("UiInputInit"), log_regs=()),
        T4Stub(fa("EvtPump"), log_regs=()),
        T4Stub(fa("UiEventPump"), fn=_pump),
        T4Stub(fa("ScreenUpdate"), log_regs=()),
        T4Stub(fa("PaletteFadeIn"), log_regs=("eax",)),
        T4Stub(fa("PaletteFadeOut"), log_regs=("eax",)),
        T4Stub(fa("ResourceFreeBody"), log_regs=()),
    ]
    t4spec.run_spec(
        os.path.join(SRC, "outro_play_flic_reference.c"), "OutroPlayFlic_", 0x188b4,
        cases, stubs=stubs, out_regs=(),
        watch=[(0x59420, 4), (0x59430, 8), (PALETTE + 723, 3),
               (LAYERS + 13 * 18, 18), (LAYERS + 14 * 18, 10), (LAYERS + 14 * 18 + 14, 4)],
        init_emu=_init_outro, log_cap=16384)
