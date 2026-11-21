import itertools
import os
import re
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_13f60')
_BY = {}


def R(name):
    if not _BY:
        _BY.update(t4spec.by_link_lenient())
    for c in (name, name + "_", "_" + name):
        if c in _BY:
            return _BY[c]["addr"]
    m = re.fullmatch(r"(?:fn|dat)_([0-9a-f]+)", name)
    if m:
        return int(m.group(1), 16)
    raise KeyError(name)


def S(name):
    return path('src/mod_13f60', name)


def mem(d):
    out = {}
    for n, (v, sz) in d.items():
        out[R(n)] = struct.pack("<I", v & 0xFFFFFFFF)[:sz]
    return out


def case(d, args=(), label=""):
    return T4Case(args=args, mem=mem(d), label=label)


def watch_of(names):
    return [(R(n), 4) for n in names]


def test_t3_files_still_match():
    t4spec.assert_t3_matches(path('src/mod_13f60'), ['choose_campaign_dialog.c', 'load_game_dialog.c', 'play_introduction.c', 'select_game_type_dialog.c', 'set_irq.c', 'set_map_dialog.c'])


def test_reference_files_still_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_13f60'), ['control_title_draw_reference.c', 'custom_game_menu_reference.c', 'main_menu_reference.c', 'save_slot_create_reference.c', 'set_army_screen_reference.c', 'set_races_screen_reference.c'])


def test_save_slot_create():
    ctx = {}

    def init_emu(emu):
        ctx["canc"] = emu.alloc(16, 16)
        ctx["errno"] = emu.alloc(16, 16)
        ctx["w"] = emu.alloc(16, 16)

    def mk_cases(r, fp, wr):
        out = []
        for dlg, scr, tbl0 in itertools.product((0, 1), (0, 1), (0, 0x41)):
            c = T4Case(args=(1, 0x2a, 0), mem={}, label=f"d{dlg}s{scr}t{tbl0}")
            c.mem = mem({"dat_516ae": (dlg, 2), "screen_mode": (scr, 2),
                         "dat_592e8": (tbl0, 4), "slot_remote": (5, 2),
                         "save_slot": (9, 2)})
            c.setup = lambda e: (e.write(ctx["canc"], b"\xff\xff"),
                                 e.write(ctx["errno"], b"\x07\0\0\0"))
            c.args = (1, 0x2a, 0)

            def st(e, c=c):
                e.write(ctx["canc"], b"\xff\xff")
                e.write(ctx["errno"], b"\x07\0\0\0")
            c.setup = st
            out.append(c)
        return out

    for r, fp, wr in itertools.product((0, 3, 7), (0, 0x1234), (0, 1)):
        cases = mk_cases(r, fp, wr)
        # cancelled pointer is allocated in init_emu; patched into args lazily
        wrapped = []
        for c in cases:
            def setup(e, c=c):
                c.args = c.args
                e.write(ctx["canc"], b"\xff\xff")
                e.write(ctx["errno"], b"\x07\0\0\0")
            c.setup = setup
            wrapped.append(c)

        def strlen_fn(e, log):
            p = e.reg("eax")
            s = e.cstr(p, 64)
            n = len(s)
            return n

        stubs = [
            T4Stub(R("SaveSlotPath"), log_regs=("edx",)),
            T4Stub(R("DialogRun"), ret=r, log_regs=("eax", "edx", "ebx", "ecx"), stack_pop=4),
            T4Stub(R("FileClose"), log_regs=()),
            T4Stub(R("FileOpen"), ret=fp, log_regs=()),
            T4Stub(R("FileWrite"), ret=wr, log_regs=("edx", "ebx")),
            T4Stub(R("__get_errno_ptr"), ret=0, log_regs=(), fn=lambda e, log: ctx["errno"]),
            T4Stub(R("strlen"), log_regs=(), fn=strlen_fn),
        ]
        # args need the cancelled pointer: build cases at run time
        final = []
        for c in wrapped:
            def setup2(e, c=c):
                e.write(ctx["canc"], b"\xff\xff")
                e.write(ctx["errno"], b"\x07\0\0\0")
            final.append(T4Case(args=(1, 0x2a, 0), mem=c.mem, setup=setup2, label=c.label))
        # run each case with the allocated pointer substituted
        class Lazy(tuple):
            pass
        def init2(emu):
            init_emu(emu)
            for fc in final:
                fc.args = (1, 0x2a, ctx["canc"])
        t4spec.run_spec(S('save_slot_create_reference.c'), 'SaveSlotCreate_', 0x14ad8, final,
                        watch=[(R("slot_remote"), 2), (R("save_slot"), 2), (R("dat_592e8"), 0xe0)],
                        stubs=stubs, init_emu=init2)


def _common_flags():
    return ["dat_516ae", "screen_mode"]


def test_control_title_draw():
    def cstr_stub(e, log):
        return None
    stubs = [
        T4Stub(R("strcpy"), log_regs=("edx",)),
        T4Stub(R("strcat"), log_regs=("edx",)),
        T4Stub(R("DrawText"), log_regs=("eax", "edx")),
        T4Stub(R("LayerInvalidate"), log_regs=("eax",)),
        T4Stub(R("BitmapClear"), log_regs=("eax",)),
        T4Stub(R("TextSetColorBase"), log_regs=("eax",)),
        T4Stub(R("TextWidth"), ret=100, log_regs=("eax",)),
    ]
    cases = []
    for a, b, s in itertools.product((0, 1), (0, 0x5000), (0, 1)):
        cases.append(case({"dat_516ae": (a, 2), "dat_5165c": (b, 4), "screen_mode": (s, 2),
                           "dat_5ab8c": (7, 2), "dat_5ab9e": (7, 2)}, label=f"{a}{b}{s}"))
    t4spec.run_spec(S('control_title_draw_reference.c'), 'ControlTitleDraw_', 0x15244, cases,
                    watch=[(R("dat_5ab8c"), 2), (R("dat_5ab9e"), 2), (R("cur_bitmap"), 4), (R("cur_font"), 4)],
                    stubs=stubs, out_regs=())


def test_main_menu():
    for r in range(0, 5):
        stubs = [
            T4Stub(R("LayerInvalidate"), log_regs=("eax",)),
            T4Stub(R("ScreenUpdate"), log_regs=()),
            T4Stub(R("SetGameMode"), log_regs=("eax",)),
            T4Stub(R("DialogRun"), ret=r, log_regs=("eax", "edx", "ebx", "ecx"), stack_pop=4),
        ]
        cases = [case({"game_mode": (g, 2), "setup_state": (0x55, 1), "dat_5ab9e": (3, 2),
                       "load_not_cancelled": (5, 2), "dialog_modal": (5, 2), "setup_quit": (5, 2),
                       "game_start_mode": (5, 2)}, label=f"g{g}") for g in (0, 9, 2)]
        t4spec.run_spec(S('main_menu_reference.c'), 'MainMenu_', 0x15588, cases,
                        watch=[(R("dat_5ab9e"), 2), (R("load_not_cancelled"), 2), (R("dialog_modal"), 2),
                               (R("setup_quit"), 2), (R("setup_state"), 1), (R("game_start_mode"), 2)],
                        stubs=stubs, out_regs=())


def test_custom_game_menu():
    for r in range(0, 6):
        stubs = [
            T4Stub(R("ControlTitleDraw"), log_regs=()),
            T4Stub(R("SetGameMode"), log_regs=("eax",)),
            T4Stub(R("NetLinkExit"), log_regs=()),
            T4Stub(R("DialogRun"), ret=r, log_regs=("eax", "edx", "ebx", "ecx"), stack_pop=4),
        ]
        cases = []
        for q, a, rs, s in itertools.product((0, 1), (0, 1), (0, 6), (0, 1)):
            cases.append(case({"setup_quit": (q, 2), "dat_516ae": (a, 2), "setup_return_state": (rs, 1),
                               "screen_mode": (s, 2), "setup_state": (0x55, 1)}, label=f"{q}{a}{rs}{s}"))
        t4spec.run_spec(S('custom_game_menu_reference.c'), 'CustomGameMenu_', 0x15898, cases,
                        watch=[(R("setup_state"), 1), (R("setup_return_state"), 1), (R("screen_mode"), 2)],
                        stubs=stubs, out_regs=())


def test_set_army_screen():
    stubs = [
        T4Stub(R("ArmyTotalsText"), log_regs=("eax",)),
        T4Stub(R("ResourceBegin"), log_regs=("eax", "edx")),
        T4Stub(R("ResourceReadHeaderBody"), log_regs=("eax", "edx")),
        T4Stub(R("LayerInvalidate"), log_regs=("eax",)),
        T4Stub(R("ArmySetupDialog"), log_regs=()),
        T4Stub(R("ControlTitleDraw"), log_regs=()),
        T4Stub(R("ResourceFreeBody"), log_regs=("eax",)),
        T4Stub(R("ScreenUpdate"), log_regs=()),
    ]
    cases = []
    for a, s, pv, oc in itertools.product((0, 1), (0, 1), (0, 1), (0, 1)):
        cases.append(case({"dat_516ae": (a, 2), "screen_mode": (s, 2), "preview_visible": (pv, 2),
                           "own_campaign": (oc, 2), "scenario_race": (1, 2), "setup_changed": (0, 2),
                           "setup_return_state": (9, 1), "setup_state": (0x55, 1),
                           "dat_592c0": (0x00500060, 4), "dat_5ab8c": (7, 2)}, label=f"{a}{s}{pv}{oc}"))
    t4spec.run_spec(S('set_army_screen_reference.c'), 'SetArmyScreen_', 0x1599c, cases,
                    watch=[(R("dat_5ab8c"), 0x18), (R("screen_mode"), 2), (R("setup_state"), 1),
                           (R("dialog_auto_update"), 2), (R("setup_changed"), 2)],
                    stubs=stubs, out_regs=())


def test_set_races_screen():
    stubs = [
        T4Stub(R("SetRacesDialog"), log_regs=()),
        T4Stub(R("ControlTitleDraw"), log_regs=()),
        T4Stub(R("ScreenUpdate"), log_regs=()),
    ]
    cases = []
    for a, s in itertools.product((0, 1), (0, 1)):
        cases.append(case({"dat_516ae": (a, 2), "screen_mode": (s, 2), "setup_changed": (0, 2),
                           "setup_return_state": (9, 1), "setup_state": (0x55, 1)}, label=f"{a}{s}"))
    t4spec.run_spec(S('set_races_screen_reference.c'), 'SetRacesScreen_', 0x15b30, cases,
                    watch=[(R("screen_mode"), 2), (R("setup_state"), 1), (R("dialog_auto_update"), 2),
                           (R("setup_changed"), 2)],
                    stubs=stubs, out_regs=())
