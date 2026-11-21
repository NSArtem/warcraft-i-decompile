import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM",
)

SRC = path("src", "mod_16390")


def ref(name):
    return os.path.join(SRC, name)


R4 = ("eax", "edx", "ebx", "ecx")
H = {}
G = (0x593e0, 0x70)          # dialog / ui / outro globals
LAYERS = 0x5aa90
CELL = 0x3f0                 # scratch cells inside the base buffer
EVT = 0x3a0                  # 12-byte event template inside the base buffer


def init_emu(emu):
    H["base"] = emu.alloc(0x1000, 16)
    H["heap"] = emu.alloc(0x1000, 16)


_LINK = {}


def A(name):
    if not _LINK:
        _LINK.update(t4spec.by_link_lenient())
    for k in (name + "_", "_" + name, name):
        if k in _LINK:
            return _LINK[k]["addr"]
    raise KeyError(name)


def ST(name, n=0, ret=0, **kw):
    a = name if isinstance(name, int) else A(name)
    return T4Stub(a, ret=ret, log_regs=R4[:n], **kw)


def SF(name, fn, **kw):
    a = name if isinstance(name, int) else A(name)
    return T4Stub(a, fn=fn, **kw)


def rd(e, a, n=4):
    return struct.unpack({1: "<B", 2: "<H", 4: "<I"}[n], e.read(a, n))[0]


def wr(e, a, fmt, *v):
    e.write(a, struct.pack("<" + fmt, *v))


def P(addr, fmt, *vals):
    return (addr, struct.pack("<" + fmt, *vals))


def memd(*pairs):
    return {a: v for a, v in pairs}


def WG(*extra):
    def g():
        yield (H["base"], 0x400)
        yield G
        for r in extra:
            yield r
    return g()


def dialog(layer=0, params=0, cb=0, items=0, unk22=0, art=0, unk16=0, unk1a=0, x=0, y=0):
    return struct.pack("<HhhIhh" + "I" * 7, layer, x, y, params, 0, 0, 0,
                       art, unk16, unk1a, cb, unk22, items)


def item(type=0, flags=0, x=0, y=0, code=0, art=0, artp=0, text=0, id=0, unk18=0, hotkey=0):
    return struct.pack("<HHhhHIIIHHH", type, flags, x, y, code, art, artp, text, id, unk18, hotkey)


def tent(type, x=0, y=0, s=0):
    return struct.pack("<HhhI", type, x, y, s)


def event(key=0, sub=3, x=7, y=8, scan=0x1c, mods=0, type=0x80):
    return struct.pack("<HHhhBBh", type, sub, x, y, scan, mods, key)


def lay(i, active=0, x=0, y=0, w=0, h=0, data=0, draw=0):
    return P(LAYERS + 18 * i, "HhhhhII", active, x, y, w, h, data, draw)


def heap_alloc(e, log):
    log(e.reg("eax"))
    return H["heap"]


def evt_fn(e, log):
    b = H["base"]
    e.write(e.reg("eax"), e.read(b + EVT, 12))
    r = rd(e, b + CELL)
    log(r)
    return r


# ---------------- guards ----------------
def test_t3_files_match():
    t4spec.assert_t3_matches(SRC, ["ui_input_init.c"])


def test_reference_files_still_mismatch():
    t4spec.assert_ref_mismatch(SRC, [
        "dialog_create_reference.c",
        "dialog_loop_reference.c",
        "dialog_relocate_reference.c",
        "ui_event_pump_net_reference.c",
        "ui_event_pump_reference.c",
        "ui_key_dispatch_reference.c",
    ])


# ---------------- DialogRelocate ----------------
def reloc_cases():
    b = H["base"]
    for with_params in (1, 0):
        pairs = [
            (b, dialog(params=(b + 0x300) if with_params else 0, cb=0x80, items=0x100,
                       unk22=0xc0, art=0x40, unk16=0x50, unk1a=0x60)),
            P(b + 0x60, "4i", 0, 0x10, -1, -1),
            P(b + 0x80, "6I", 0x20, 1, 2, 3, 0xffffffff, 1),
            P(b + 0x300, "8I", *[0x11110000 + i for i in range(8)]),
        ]
        if with_params:
            pairs.append((b + 0xc0, tent(3, 0, 0, 1) + tent(1, 0, 0, 0x10) + tent(0xffff)))
            its = [item(0, text=0x10), item(3, art=0x20, artp=0x30, text=0x40),
                   item(5, art=0x20, artp=0x30, text=0x44), item(7, id=0x50, text=0x60),
                   item(11, art=4, text=2), item(8, art=0x20, artp=0x30, text=0x70),
                   item(4, art=0x20, artp=0x30), item(0xffff)]
        else:
            pairs.append((b + 0xc0, tent(1, 0, 0, 0x10) + tent(0xffff)))
            its = [item(0, text=0x10), item(6, text=0x20), item(10, id=0x50, text=0x60), item(0xffff)]
        pairs.append((b + 0x100, b"".join(its)))
        yield T4Case(args=(b,), mem=memd(*pairs), label="params=%d" % with_params)


def test_dialog_relocate():
    t4spec.run_spec(ref("dialog_relocate_reference.c"), "DialogRelocate_", 0x166bc,
                    reloc_cases(), watch=WG(), out_regs=(), init_emu=init_emu)


# ---------------- DialogCreate ----------------
def create_cases():
    b = H["base"]
    for artdata in (b + 0x300, 0):
        pairs = [
            (b, dialog(layer=3, x=10, y=20, art=b + 0x40, cb=b + 0x80, unk22=b + 0xc0)),
            (b + 0x40, struct.pack("<hHI", 0xf5, 1, 0) + struct.pack("<hHI", 0x10, 2, 0)
             + struct.pack("<hHI", -1, 0, 0)),
            P(b + 0x80, "I", b + 0x100),
            P(b + 0x100, "HHI", 0x40, 0x20, b + 0x340),
            (b + 0xc0, tent(0, 5, 6, b + 0x200) + tent(4, 1, 2, b + 0x100)
             + tent(2, 30, 6, b + 0x200) + tent(3, 40, 9, b + 0x200) + tent(0xffff)),
            P(b + 0x200, "8s", b"Hi"),
            P(0x593e0, "HHI", 0x30, 0x10, 0),
            P(0x593e4, "I", artdata),
        ]
        yield T4Case(args=(b,), mem=memd(*pairs), label="art=%x" % (artdata != 0))


def test_dialog_create():
    stubs = [
        SF("GdsAlloc", heap_alloc),
        ST("memcpy", 3), ST("ResourceBegin", 2), ST("ResourceReadHeaderBody", 2),
        ST("LayerInvalidate", 1), ST("BitmapClear", 1), ST("DialogCallOpen", 1),
        ST("TextSetColorBase", 1), ST("BitmapBlitTransparentAll", 3),
        ST("TextWidth", 2, ret=11), ST("DrawText", 3), ST("DialogDrawItems", 1),
    ]
    t4spec.run_spec(ref("dialog_create_reference.c"), "DialogCreate_", 0x168b4,
                    create_cases(), watch=WG((LAYERS, 576), (0x55438, 4), (0x5acf0, 4)),
                    stubs=stubs, out_regs=(), init_emu=init_emu)


# ---------------- DialogLoop ----------------
def loop_cases():
    b = H["base"]

    def mk(label, key=0, lb=0, hit=0, loopret=0, done=0, quit=0, d59614=0):
        pairs = [
            (b, dialog(cb=b + 0x200, items=b + 0x40)),
            (b + 0x40, item(0, hotkey=0x41) + item(6, hotkey=0x7e) + item(4, hotkey=0x4800)
             + item(0xffff)),
            P(b + 0x200, "IHH", 0, 0x11, 0x22),
            P(b + 0x3f0, "hh", key, lb),
            P(b + 0x3f4, "I", hit),
            P(b + 0x3f8, "I", (b + 0x40) if loopret else 0),
            P(b + 0x3fc, "I", done),
            P(0x5176a, "h", quit),
            P(0x59614, "I", d59614),
        ]
        return T4Case(args=(b,), mem=memd(*pairs), label=label)

    yield mk("quit", quit=1)
    yield mk("d59614", d59614=9 << 16)
    yield mk("done", done=1)
    yield mk("enter", key=0x0d)
    yield mk("enter-hit", key=0x0d, hit=1)
    yield mk("esc", key=0x1b)
    yield mk("up", key=0x4800)
    yield mk("down", key=0x7c00)
    yield mk("hotkey", key=0x41)
    yield mk("hotkey-any", key=0x7e)
    yield mk("left", lb=1, loopret=1, hit=1)


def test_dialog_loop():
    def kill(e, log):
        log(e.reg("eax"), e.reg("edx"))
        wr(e, 0x593fa, "h", 0)

    def pump(e, log):
        b = H["base"]
        wr(e, 0x593f8, "h", rd(e, b + 0x3f0, 2))
        wr(e, 0x593fc, "h", rd(e, b + 0x3f2, 2))
        log(0)

    def itemloop(e, log):
        log(e.reg("eax"))
        wr(e, 0x593fa, "h", 0)
        return rd(e, H["base"] + 0x3f8)

    def hittest(e, log):
        log(e.reg("eax"), e.reg("edx"))
        return rd(e, H["base"] + 0x3f4)

    def done(e, log):
        log(e.reg("eax"))
        return rd(e, H["base"] + 0x3fc)

    stubs = [
        SF("UiEventPumpNet", pump), ST("DialogPreviewCursor", 0), ST("ScreenUpdate", 0),
        SF("DialogCheckDone", done), SF("ListScrollBy", kill), SF("DialogActivateItem", kill),
        SF("DialogItemLoop", itemloop), SF("DialogItemHitTest", hittest),
        ST("DialogDrawItemState", 4),
    ]
    t4spec.run_spec(ref("dialog_loop_reference.c"), "DialogLoop_", 0x17e54,
                    loop_cases(), watch=WG(), stubs=stubs, out_regs=(), init_emu=init_emu)


# ---------------- UiKeyDispatch ----------------
def key_cases():
    b = H["base"]
    rows = [
        (4, 0x32, 0, 0, 0, 1), (4, 0x32, 0, 1, 0, 1), (4, 0x32, 0, 1, 1, 1),
        (8, 0x32, 0, 0, 0, 1), (4, 0x1f, 0, 0, 0, 1), (4, 0x1f, 0, 1, 0, 1),
        (4, 0x1f, 0, 1, 1, 1), (0, 0x1c, 0, 0, 0, 1), (0, 0x1c, 0, 0, 0, 0),
        (0, 0x1c, 1, 0, 0, 1), (8, 0x1c, 0, 0, 0, 1),
    ]
    for mods, scan, bits, fwd, smode, hnd in rows:
        pairs = [
            (b, event(scan=scan, mods=mods, type=0x80, sub=0)),
            P(0x5942e, "H", bits), P(0x5942c, "h", fwd), P(0x593f6, "H", smode),
            P(0x59400, "I", A("DialogKeyHandler") if hnd else 0),
        ]
        yield T4Case(args=(b,), mem=memd(*pairs),
                     label="m%x s%x b%d f%d sm%d h%d" % (mods, scan, bits, fwd, smode, hnd))


def test_ui_key_dispatch():
    stubs = [ST("SndToggleMusic", 0), ST("SndToggleSfx", 0), ST(0x13e94, 0),
             T4Stub(A("DialogKeyHandler"), log_regs=("eax",))]
    t4spec.run_spec(ref("ui_key_dispatch_reference.c"), "UiKeyDispatch_", 0x182e4,
                    key_cases(), watch=WG(), stubs=stubs, out_regs=(), init_emu=init_emu)


# ---------------- UiEventPump / UiEventPumpNet ----------------
def pump_mem(eq, ok, pre, hnd, net=0, smode=0):
    b = H["base"]
    rx, ry = (11, 22) if eq else (50, 60)
    return memd(
        P(0x5aa78, "B", 2), lay(2, 1, 10, 20, 4, 4),
        P(0x5aa60, "hh", 1, 2), P(0x5a8b0, "hh", rx, ry),
        (b + EVT, event(sub=3, x=7, y=8)), P(b + CELL, "I", ok),
        P(0x51770, "10I", *[0, 0, 0, A("DialogKeyHandler") if hnd else 0, 0, 0, 0, 0, 0, 0]),
        P(0x59424, "I", A("DialogIdleHandler") if pre else 0),
        P(0x52586, "h", net), P(0x593f6, "H", smode),
    )


def pump_cases():
    for eq, ok, pre, hnd in ((1, 1, 1, 1), (0, 1, 1, 1), (1, 0, 0, 0), (0, 0, 1, 0),
                             (1, 1, 0, 1), (1, 1, 1, 0)):
        yield T4Case(args=(), mem=pump_mem(eq, ok, pre, hnd),
                     label="eq%d ok%d pre%d h%d" % (eq, ok, pre, hnd))


def pump_net_cases():
    for net, sm in ((0, 0), (1, 1), (1, 0)):
        for eq in (1, 0):
            for ok in (1, 0):
                yield T4Case(args=(), mem=pump_mem(eq, ok, 1, 1, net, sm),
                             label="net%d sm%d eq%d ok%d" % (net, sm, eq, ok))


def test_ui_event_pump():
    stubs = [ST("CursorMoveTo", 2), SF("EvtGet", evt_fn), T4Stub(A("EvtProcess"), log_regs=()),
             T4Stub(A("DialogKeyHandler"), log_regs=()), ST("DialogIdleHandler", 0)]
    t4spec.run_spec(ref("ui_event_pump_reference.c"), "UiEventPump_", 0x184cc,
                    pump_cases(), watch=WG((LAYERS, 576)), stubs=stubs, out_regs=(),
                    init_emu=init_emu)


def test_ui_event_pump_net():
    stubs = [ST("CursorMoveTo", 2), SF("EvtGet", evt_fn),
             SF("NetSendLocalEvent", evt_fn), SF("NetQueryRemoteEvent", evt_fn),
             T4Stub(A("EvtProcess"), log_regs=()),
             T4Stub(A("DialogKeyHandler"), log_regs=()), ST("DialogIdleHandler", 0)]
    t4spec.run_spec(ref("ui_event_pump_net_reference.c"), "UiEventPumpNet_", 0x185b4,
                    pump_net_cases(), watch=WG((LAYERS, 576)), stubs=stubs, out_regs=(),
                    init_emu=init_emu)
