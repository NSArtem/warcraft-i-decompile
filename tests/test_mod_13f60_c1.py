import os
import struct
from functools import lru_cache

import pytest

from wc1 import cemu, path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')),
    reason='needs original/ and $WATCOM',
)

T3_FILES = [
    'army_labels_draw.c',
    'map_choice_dungeon.c',
    'map_choice_random.c',
    'map_choice_refresh.c',
    'map_choice_swamp.c',
    'preview_rect_update.c',
    'preview_toggle.c',
    'save_slot_open.c',
    'set_races_dialog.c',
]
REF_FILES = [
    'army_setup_dialog_reference.c',
    'save_slots_scan_reference.c',
]

D = path('src', 'mod_13f60')
S = {}
CFG = {}


def src(n):
    return os.path.join(D, n)


@lru_cache(maxsize=None)
def A(name):
    return t4spec.by_link_lenient()["_" + name]["addr"]


def w16(emu, name, v):
    emu.write(A(name), struct.pack("<H", v & 0xFFFF))


def init_emu(emu):
    S["dlg"] = emu.alloc(0x40, 16)
    S["text"] = emu.alloc(0x200, 16)
    S["canc"] = emu.alloc(16, 16)
    S["errno"] = emu.alloc(16, 16)


def test_t3_files_match():
    if T3_FILES:
        t4spec.assert_t3_matches(path('src/mod_13f60'), T3_FILES)


def test_reference_files_still_mismatch():
    if REF_FILES:
        t4spec.assert_ref_mismatch(path('src/mod_13f60'), REF_FILES)


# ---------------------------------------------------------------- SaveSlotsScan
def _scan_case(remote, camp, scr, fopen, rd_ok, magic_ok, label):
    def setup(emu):
        emu.write(A("army_setup") + 0x16, struct.pack("<I", S["text"]))
        emu.write(S["text"], b"\xaa" * 0x200)
        emu.write(0x516ae, struct.pack("<H", camp))
        emu.write(0x593f6, struct.pack("<H", scr))
        emu.write(0x593d6, struct.pack("<H", remote))
        emu.write(0x59290 + 0x58, b"\x55" * 0xe0)
        CFG.update(fopen=fopen, rd_ok=rd_ok, magic_ok=magic_ok)
    return T4Case(args=(A("army_setup"),), setup=setup, label=label)


def test_save_slots_scan():
    def rd(e, log):
        buf = e.reg("eax")
        size = e.reg("edx")
        log(size, e.reg("ebx"), e.reg("ecx"))
        if not CFG.get("rd_ok", 1):
            return 0
        if size == 4:
            m = 0x31726157 if CFG.get("magic_ok", 1) else 0x12345678
            e.write(buf, struct.pack("<I", m))
        elif size == 0x20:
            e.write(buf, b"Slot name\x00".ljust(0x20, b"\x00"))
        return 1

    def fopen(e, log):
        log(e.reg("edx"))
        return 0x1234 if CFG.get("fopen", 1) else 0

    bl = cemu._by_link()
    stubs = [
        T4Stub(bl["SaveSlotPath_"]["addr"], log_regs=("edx",)),
        T4Stub(bl["FileOpen_"]["addr"], fn=fopen),
        T4Stub(bl["FileRead_"]["addr"], fn=rd),
        T4Stub(bl["FileSeek_"]["addr"], log_regs=("edx", "ebx")),
        T4Stub(bl["FileClose_"]["addr"], log_regs=("eax",)),
    ]
    cases = []
    for remote in (0, 1):
        for camp, scr in ((0, 0), (1, 0), (1, 1)):
            for fo, ok, mg in ((1, 1, 1), (0, 1, 1), (1, 0, 1), (1, 1, 0)):
                cases.append(_scan_case(remote, camp, scr, fo, ok, mg, f"r{remote}c{camp}s{scr}f{fo}{ok}{mg}"))
    t4spec.run_spec(
        src('save_slots_scan_reference.c'), 'SaveSlotsScan_', 0x147a8, cases,
        out_regs=(), stubs=stubs, init_emu=init_emu, log_cap=2048, extra={'_cd_14668': 0x14668},
        watch=[(0x59290 + 0x58, 0xe0)],
    )


# ---------------------------------------------------------------- PreviewRectUpdate
def test_preview_rect_update():
    def mk(vals, label):
        def setup(emu):
            for i, v in enumerate(vals):
                emu.write(0x5ab8e + 2 * i, struct.pack("<h", v))
            emu.write(0x5175c, b"\xcc" * 12)
        return T4Case(setup=setup, label=label)

    def gen(rng):
        return mk([rng.randint(-32768, 32767) for _ in range(4)], "")

    cases = [
        mk([0, 0, 0, 0], "zero"),
        mk([10, 20, 30, 40], "basic"),
        mk([-5, -6, 7, 8], "neg"),
        mk([32767, 32767, 32767, 32767], "ovf"),
    ]
    t4spec.run_spec(
        src('preview_rect_update.c'), 'PreviewRectUpdate_', 0x14ca8, cases,
        out_regs=(), watch=[(0x5175c, 12)], rand_cases=16, rand_gen=gen,
    )


# ---------------------------------------------------------------- ArmyLabelsDraw
def test_army_labels_draw():
    def mk(camp, own, label):
        def setup(emu):
            emu.write(0x516ae, struct.pack("<H", camp))
            emu.write(0x52584, struct.pack("<H", own))
        return T4Case(setup=setup, label=label)

    bl = cemu._by_link()
    cases = [mk(0, 0, "off"), mk(1, 0, "c1o0"), mk(1, 1, "c1o1"), mk(0, 1, "c0o1")]
    watch = [(A("cur_bitmap"), 4)]
    t4spec.run_spec(
        src('army_labels_draw.c'), 'ArmyLabelsDraw_', 0x14d68, cases,
        out_regs=(), watch=watch,
        stubs=[T4Stub(bl["DrawText_"]["addr"], log_regs=("eax", "edx", "ebx"))],
        log_cap=2048,
    )


# ---------------------------------------------------------------- PreviewToggle
def test_preview_toggle():
    bl = cemu._by_link()

    def mk(v, label):
        def setup(emu):
            w16(emu, "preview_visible", v)
            emu.write(0x5ab8c, b"\x99\x99")
        return T4Case(setup=setup, label=label)

    t4spec.run_spec(
        src('preview_toggle.c'), 'PreviewToggle_', 0x14e48,
        [mk(0, "off"), mk(1, "on"), mk(7, "other")], out_regs=(),
        watch=[(A("preview_visible"), 2), (0x5ab8c, 2)],
        stubs=[
            T4Stub(bl["PreviewRectReset_"]["addr"], log_regs=()),
            T4Stub(bl["PreviewRectUpdate_"]["addr"], log_regs=()),
            T4Stub(bl["LayerInvalidate_"]["addr"], log_regs=("eax",)),
        ],
    )


# ---------------------------------------------------------------- ArmySetupDialog
def test_army_setup_dialog():
    bl = cemu._by_link()

    def dlg(e, log):
        log(e.reg("eax"), e.reg("edx"), e.reg("ebx"), e.reg("ecx"))
        return CFG.get("ret", 0)

    def mk(camp, own, r, re_, vis, ret, label):
        def setup(emu):
            CFG["ret"] = ret
            emu.write(0x516ae, struct.pack("<H", camp))
            emu.write(0x52584, struct.pack("<H", own))
            w16(emu, "scenario_race", r)
            w16(emu, "scenario_race_enemy", re_)
            w16(emu, "preview_visible", vis)
            w16(emu, "setup_changed", 0)
            emu.write(A("setup_return_state"), b"\x00")
            emu.write(A("army_setup"), struct.pack("<19I", *range(1, 20)))
        return T4Case(setup=setup, label=label)

    cases = []
    for camp in (0, 1):
        for own in (0, 1):
            for r, re_ in ((0, 0), (1, 0), (0, 1), (1, 1)):
                for vis in (0, 1):
                    for ret in (0, 1):
                        cases.append(mk(camp, own, r, re_, vis, ret, f"c{camp}o{own}r{r}{re_}v{vis}x{ret}"))
    t4spec.run_spec(
        src('army_setup_dialog_reference.c'), 'ArmySetupDialog_', 0x14e9c, cases,
        out_regs=(), log_cap=4096,
        watch=[(A("army_setup"), 0x4c), (A("setup_changed"), 2), (A("setup_return_state"), 1)],
        stubs=[
            T4Stub(bl["PreviewRectReset_"]["addr"], log_regs=()),
            T4Stub(bl["PreviewRectUpdate_"]["addr"], log_regs=()),
            T4Stub(bl["DialogRun_"]["addr"], fn=dlg, stack_pop=4),
        ],
    )
