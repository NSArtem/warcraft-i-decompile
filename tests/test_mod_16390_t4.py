"""T4 differential tests for mod_16390 reference C vs original machine code."""
import os
import struct

import pytest

try:
    from wc1 import path, t4spec
    from wc1.emu import Emu
    HAVE = True
except Exception:  # pragma: no cover
    HAVE = False

pytestmark = pytest.mark.skipif(
    not HAVE or not os.path.isdir(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src", "mod_16390")),
    reason="wc1 harness or mod_16390 sources unavailable")

# data addresses (from the symbol DB)
LAST_KEY = 0x593f8
SOUNDS = 0x593f4
MOUSE_X = 0x59428
MOUSE_Y = 0x5942a
BTN_BITS = 0x5942e
LEFT_PRESS = 0x59410
STATUS_FRAME = 0x59414
RIGHT_PRESS = 0x59418
STATUS_CLICK = 0x5941c
DIALOG_IDLE = 0x59420
DEFAULT_FONT = 0x55444
CUR_BITMAP = 0x55438
CUR_FONT = 0x5acf0
LAYER_X = 0x5aa92
LAYER_Y = 0x5aa94

# function addresses used as stub targets
LIST_DRAW = 0x163c8
FN_13E94 = 0x13e94
FN_13E60 = 0x13e60
DRAW_TEXT = 0x31dcc
BITMAP_CLEAR = 0x31fc0


def _alloc(emu):
    return {
        "dlg": emu.alloc(32, 16), "item": emu.alloc(32, 16),
        "art": emu.alloc(16, 16), "params": emu.alloc(128, 16),
        "texts": emu.alloc(64, 16), "font": emu.alloc(16, 16),
        "ev": emu.alloc(16, 16), "tb": emu.alloc(1024, 16),
    }


ENV = _alloc(Emu()) if HAVE else {}


def _init(emu):
    assert _alloc(emu) == ENV


def _w(emu, addr, fmt, val):
    emu.write(addr, struct.pack("<" + fmt, val & {"B": 0xFF, "H": 0xFFFF, "I": 0xFFFFFFFF}[fmt]))


def S(layer=0, dy=0, flags=0, x=0, y=0, w=0, h=0, text=0, texts=None,
      id=0, params=(), rows=0, glob=(), layers=None, ev=None, string=None):
    def f(emu):
        E = ENV
        _w(emu, E["dlg"], "H", layer)
        _w(emu, E["dlg"] + 4, "H", dy)
        _w(emu, E["dlg"] + 6, "I", E["params"])
        _w(emu, E["item"] + 2, "B", flags)
        _w(emu, E["item"] + 4, "H", x)
        _w(emu, E["item"] + 6, "H", y)
        _w(emu, E["item"] + 0xa, "I", E["art"])
        t = text
        if texts is not None:
            t = E["texts"]
            for i, v in enumerate(texts):
                _w(emu, E["texts"] + 4 * i, "I", v)
        _w(emu, E["item"] + 0x12, "I", t)
        _w(emu, E["item"] + 0x16, "H", id)
        _w(emu, E["art"], "H", w)
        _w(emu, E["art"] + 2, "H", h)
        emu.write(E["params"], b"\x00" * 128)
        for i, v in enumerate(params):
            _w(emu, E["params"] + 4 * i, "I", v)
        _w(emu, E["font"] + 2, "B", rows)
        if layers:
            for ly, lx, lyy in layers:
                _w(emu, LAYER_X + ly * 18, "H", lx)
                _w(emu, LAYER_Y + ly * 18, "H", lyy)
        if ev is not None:
            _w(emu, E["ev"] + 2, "H", ev[0])
            _w(emu, E["ev"] + 0xa, "H", ev[1])
        for a, fmt, v in glob:
            _w(emu, a, fmt, v)
        if string is not None:
            emu.write(E["tb"], string + b"\x00")
    return f


def C(label, setup, args=None):
    return t4spec.T4Case(args=args if args is not None else (ENV["dlg"], ENV["item"]),
                         setup=setup, label=label)


def run(src, name, addr, cases, **kw):
    # Watcom register-convention link names carry a trailing underscore
    if not name.endswith("_"):
        name = name + "_"
    t4spec.run_spec(path("src", "mod_16390", src), name, addr, cases,
                    init_emu=_init, **kw)


PARAMS_W = [(ENV.get("params", 0), 128)]


def test_list_selected_text():
    cases = []
    for id_ in (0, 1, 2):
        for sel in (0, 1, 3, 7):
            # params viewed as u16 array indexed id*2
            p = [0] * 8
            p[id_] = sel | 0xABCD0000
            cases.append(C("id%d sel%d" % (id_, sel),
                           S(id=id_, params=p,
                             texts=[0x1000 + i for i in range(16)])))
    run("list_selected_text_reference.c", "ListSelectedText", 0x163a8, cases)


def test_dialog_key_handler():
    cases = []
    for sub in (1, 2, 3):
        for key in (0, 0x40, 0x41, 0x60, 0x61, 0x6d, 0x7a, 0x7b, 0x7f, 0xff, -1, 0x1b):
            cases.append(C("sub%d key%d" % (sub, key),
                           S(ev=(sub, key), glob=[(LAST_KEY, "H", 0x1234)]),
                           args=(ENV["ev"],)))
    run("dialog_key_handler_reference.c", "DialogKeyHandler", 0x16c58, cases,
        watch=[(LAST_KEY, 2)], out_regs=())


def test_dialog_item_hit_test():
    cases = []
    lay = [(0, 100, 50), (1, 5, 7), (2, 0, 0)]
    for layer, lx, ly in lay:
        for mx in (lx + 10 - 1, lx + 10, lx + 15, lx + 29, lx + 30, 0, 0xffff):
            for my in (ly + 5 - 1, ly + 5, ly + 9, ly + 12, ly + 13, 0, 0xffff):
                cases.append(C("L%d %d,%d" % (layer, mx, my),
                               S(layer=layer, x=10, y=5, w=20, h=8, layers=lay,
                                 glob=[(MOUSE_X, "H", mx), (MOUSE_Y, "H", my)])))
    cases.append(C("neg pos", S(layer=0, x=0xfff0, y=0xfff0, w=20, h=20,
                                layers=[(0, 0, 0)],
                                glob=[(MOUSE_X, "H", 0xfff8), (MOUSE_Y, "H", 0xfff8)])))
    run("dialog_hit_test_reference.c", "DialogItemHitTest", 0x16cc8, cases)


def _snd_addr():
    e = t4spec.by_link_lenient().get("SndPlay_")
    if not e:
        pytest.skip("SndPlay_ not in symbol DB")
    return e["addr"]


def _highlight(name, addr):
    snd = _snd_addr()
    cases = [C("loaded=%d" % v, S(glob=[(SOUNDS, "H", v)]), args=())
             for v in (0, 1, 0x100, 0xffff)]
    run("dialog_hit_test_reference.c", name, addr, cases,
        stubs=[t4spec.T4Stub(snd, log_regs=("eax",))], out_regs=())


def test_dialog_highlight_on():
    _highlight("DialogHighlightOn", 0x16d34)


def test_dialog_highlight_off():
    _highlight("DialogHighlightOff", 0x16d48)


def test_list_select_at_mouse():
    cases = []
    glob0 = [(DEFAULT_FONT, "I", ENV["font"])]
    for tx in ([0x2000, 0x2001, 0x2002, 0xFFFFFFFF], [0, 0xFFFFFFFF],
               [0x2000, 0xFFFFFFFF]):
        for id_ in (0, 2):
            for my in (0, 27, 28, 37, 38, 47, 48, 57, 58, 0xffff):
                cases.append(C("tx%d id%d my%d" % (len(tx), id_, my),
                               S(dy=20, y=5, id=id_, rows=10, texts=tx,
                                 params=[9, 9, 9, 9],
                                 glob=glob0 + [(MOUSE_Y, "H", my)])))
    # edx is not a real argument of the stubbed callee (stale register), so
    # only eax is compared
    run("list_select_at_mouse_reference.c", "ListSelectAtMouse", 0x16eb0, cases,
        watch=[(ENV["params"], 128)],
        stubs=[t4spec.T4Stub(LIST_DRAW, log_regs=("eax",))], out_regs=())


def test_list_sel_prev():
    cases = []
    for sel in (0, 1, 2, 5, 0x80000000, 0xffffffff):
        for flags in (0, 1, 2, 3):
            for text in (0, 1, 4):
                for id_ in (0, 2):
                    p = [7, 7, 7, 7]
                    p[id_] = sel
                    cases.append(C("sel%x f%d t%d id%d" % (sel, flags, text, id_),
                                   S(id=id_, flags=flags, text=text, params=p)))
    run("list_sel_prev_reference.c", "ListSelPrev", 0x17430, cases,
        watch=[(ENV["params"], 128)], out_regs=())


def test_list_sel_next():
    cases = []
    for sel in (0, 1, 2, 3, 5, 0x80000000, 0xffffffff):
        for flags in (0, 1, 2, 3):
            for text in (0, 1, 3):
                for id_ in (0, 2):
                    p = [7, 7, 7, 7]
                    p[id_] = sel
                    cases.append(C("sel%x f%d t%d id%d" % (sel, flags, text, id_),
                                   S(id=id_, flags=flags, text=text, params=p)))
    run("list_sel_next_reference.c", "ListSelNext", 0x1746c, cases,
        watch=[(ENV["params"], 128)], out_regs=())


def test_ui_button_press():
    cases = []
    for bits in (0, 1, 2, 3):
        for sub in (3, 4, 5, 6, 7):
            for lp, rp in ((LIST_DRAW, FN_13E60), (0, 0), (LIST_DRAW, 0), (0, FN_13E60)):
                cases.append(C("bits%d sub%d lp%x rp%x" % (bits, sub, lp, rp),
                               S(ev=(sub, 0),
                                 glob=[(BTN_BITS, "H", bits), (LEFT_PRESS, "I", lp),
                                       (RIGHT_PRESS, "I", rp)]),
                               args=(ENV["ev"],)))
    run("ui_button_press_reference.c", "UiButtonPress", 0x18398, cases,
        watch=[(BTN_BITS, 2)],
        stubs=[t4spec.T4Stub(FN_13E94, log_regs=()),
               t4spec.T4Stub(LIST_DRAW, log_regs=()),
               t4spec.T4Stub(FN_13E60, log_regs=())],
        out_regs=())


def test_ui_button_release():
    cases = []
    for bits in (0, 1, 2, 3, 0x103):
        for sub in (3, 4, 5, 6, 7):
            for fr, cl in ((DRAW_TEXT, BITMAP_CLEAR), (0, 0), (DRAW_TEXT, 0), (0, BITMAP_CLEAR)):
                cases.append(C("bits%x sub%d fr%x cl%x" % (bits, sub, fr, cl),
                               S(ev=(sub, 0),
                                 glob=[(BTN_BITS, "H", bits), (STATUS_FRAME, "I", fr),
                                       (STATUS_CLICK, "I", cl)]),
                               args=(ENV["ev"],)))
    run("ui_button_release_reference.c", "UiButtonRelease", 0x183e8, cases,
        watch=[(BTN_BITS, 2)],
        stubs=[t4spec.T4Stub(FN_13E94, log_regs=()),
               t4spec.T4Stub(DRAW_TEXT, log_regs=()),
               t4spec.T4Stub(BITMAP_CLEAR, log_regs=())],
        out_regs=())


def test_ui_frame():
    cases = [C("idle=%x" % v, S(glob=[(DIALOG_IDLE, "I", v)]), args=(ENV["ev"],))
             for v in (0, LIST_DRAW)]
    run("ui_frame_reference.c", "UiFrame", 0x18470, cases,
        stubs=[t4spec.T4Stub(FN_13E60, log_regs=()),
               t4spec.T4Stub(LIST_DRAW, log_regs=())],
        out_regs=())


def _draw_text(emu, log):
    s = b""
    a = emu.reg("ebx")
    while len(s) < 0x50:
        c = emu.read(a + len(s), 1)
        if c == b"\x00":
            break
        s += c
    log(emu.reg("eax"), emu.reg("edx"), len(s), sum(s) + 31 * len(s))
    return 0


def test_outro_draw_text_page():
    texts = [
        b"A",
        b"hello\nworld",
        b"one\r\ntwo\r\nthree\r\n",
        b"\n\n\nx\n",
        b"line\r\n" * 5,
        b"".join(b"L%d\r\n" % i for i in range(20)),
        b"".join(b"L%d\n" % i for i in range(14)),
        b"".join(b"L%d\n" % i for i in range(15)) + b"tail",
        b"no newline at all",
        b"\r\rabc\rdef\n\nghi",
    ]
    cases = []
    for i, t in enumerate(texts):
        for rows in (0, 9, 16):
            cases.append(C("text%d rows%d" % (i, rows),
                           S(rows=rows, string=t,
                             glob=[(CUR_FONT, "I", ENV["font"])]),
                           args=(ENV["art"], ENV["tb"])))
    run("outro_draw_text_page_reference.c", "OutroDrawTextPage", 0x18810, cases,
        watch=[(CUR_BITMAP, 4)],
        stubs=[t4spec.T4Stub(BITMAP_CLEAR, log_regs=("eax",)),
               t4spec.T4Stub(DRAW_TEXT, fn=_draw_text)])
