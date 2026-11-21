import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.emu import Emu
from wc1.t4spec import T4Stub, T4Case

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_13f60')
_BL = None


def _bl():
    global _BL
    if _BL is None:
        _BL = t4spec.by_link_lenient()
    return _BL


def A(name):
    """Address of a symbol by DB name (function or data)."""
    bl = _bl()
    for cand in (name + "_", "_" + name, name):
        if cand in bl:
            return bl[cand]["addr"]
    raise AssertionError("symbol not in DB: " + name)


def W(name, size):
    return (A(name), size)


def _dialog_stub(holder, addr):
    def fn(e, log):
        log(e.reg("eax"), e.reg("edx"), e.reg("ebx"), e.reg("ecx"))
        return holder["r"]
    return T4Stub(addr, fn=fn, stack_pop=4)


def _cases(setup_fn, rs):
    out = []
    for r in rs:
        out.append(T4Case(setup=setup_fn(r), label="r=%d" % r))
    return out


def test_t3_files_match():
    files = ['choose_campaign_dialog.c', 'connection_failed.c',
             'network_connection_dialog.c', 'set_map_screen.c']
    if files:
        t4spec.assert_t3_matches(SRC, files)


def test_reference_files_still_mismatch():
    files = ['direct_connection_dialog_reference.c', 'modem_connection_dialog_reference.c',
             'modem_setup_dialog_reference.c', 'net_game_start_reference.c',
             'select_game_type_dialog_reference.c', 'setup_menu_loop_reference.c']
    if files:
        t4spec.assert_ref_mismatch(SRC, files)


def test_select_game_type_dialog():
    holder = {"r": 0}
    gsm = 0x593d4

    def mk(r):
        def setup(emu):
            holder["r"] = r
        return setup

    cases = []
    for gs in (0, 1, 2):
        for r in range(0, 6):
            def setup(emu, r=r, gs=gs):
                holder["r"] = r
                emu.write(gsm, struct.pack("<H", gs))
                emu.write(A("connection_type"), struct.pack("<H", 7))
                emu.write(A("setup_state"), b"\x55")
            cases.append(T4Case(setup=setup, label="gs=%d r=%d" % (gs, r)))
    t4spec.run_spec(
        os.path.join(SRC, "select_game_type_dialog_reference.c"),
        "SelectGameTypeDialog_", 0x15668, cases,
        out_regs=(),
        watch=[(gsm, 2), W("custom_game", 2), W("connection_type", 2),
               W("net_modem_link", 2), W("setup_state", 1)],
        stubs=[_dialog_stub(holder, A("DialogRun"))])


def test_modem_connection_dialog():
    holder = {"r": 0}
    cases = []
    for init in (0, 1):
        for r in range(0, 4):
            def setup(emu, r=r, init=init):
                holder["r"] = r
                emu.write(A("modem_setup_init"), struct.pack("<H", init))
                emu.write(A("net_settings"), struct.pack("<8I", *range(1, 9)))
                emu.write(0x592c8, struct.pack("<8I", *range(0, 8)))
                emu.write(A("modem_port"), struct.pack("<I", 0x00030002))
                emu.write(A("modem_baud"), struct.pack("<I", 9600))
            cases.append(T4Case(setup=setup, label="init=%d r=%d" % (init, r)))
    t4spec.run_spec(
        os.path.join(SRC, "modem_connection_dialog_reference.c"),
        "ModemConnectionDialog_", 0x15ca8, cases,
        out_regs=(),
        watch=[W("net_settings", 32), (0x592c8, 32), W("modem_setup_init", 2),
               W("setup_state", 1), W("modem_port", 4), W("modem_baud", 4),
               W("modem_irq", 2), W("net_side", 1), W("edit_char_hook", 4),
               (0x52584, 2)],
        stubs=[_dialog_stub(holder, A("DialogRun")),
               T4Stub(A("BaudToIndex"), ret=3, log_regs=("eax",)),
               T4Stub(A("IndexToBaud"), ret=2400, log_regs=("eax",)),
               T4Stub(A("IrqToIndex"), ret=2, log_regs=("eax",)),
               T4Stub(A("IndexToIrq"), ret=5, log_regs=("eax",)),
               T4Stub(0x1d538, log_regs=())])


def test_modem_setup_dialog():
    holder = {"r": 0}
    cases = []
    for dp in (0, 1, 5):
        for r in (0, 1):
            def setup(emu, r=r, dp=dp):
                holder["r"] = r
                emu.write(A("dial_pulse"), bytes([dp]))
                emu.write(0x59230, b"ATZ\x00")
                emu.write(0x59260, b"INIT2\x00")
                emu.write(0x59290, b"HANG\x00")
            cases.append(T4Case(setup=setup, label="dp=%d r=%d" % (dp, r)))
    t4spec.run_spec(
        os.path.join(SRC, "modem_setup_dialog_reference.c"),
        "ModemSetupDialog_", 0x15e1c, cases,
        out_regs=(),
        watch=[W("dial_pulse", 1), W("setup_state", 1), (0x52998, 0x30),
               (0x529c8, 0x30), (0x529f8, 0x30)],
        stubs=[_dialog_stub(holder, A("DialogRun")),
               T4Stub(0x1d538, log_regs=())])


def test_direct_connection_dialog():
    holder = {"r": 0}
    cases = []
    for r in (0, 1, 2):
        def setup(emu, r=r):
            holder["r"] = r
            emu.write(A("serial_port"), struct.pack("<I", 0x00020003))
            emu.write(A("serial_baud"), struct.pack("<I", 19200))
        cases.append(T4Case(setup=setup, label="r=%d" % r))
    t4spec.run_spec(
        os.path.join(SRC, "direct_connection_dialog_reference.c"),
        "DirectConnectionDialog_", 0x16044, cases,
        out_regs=(),
        watch=[W("serial_baud", 4), W("serial_port", 4), W("serial_irq", 2),
               W("setup_state", 1), (0x52584, 2)],
        stubs=[_dialog_stub(holder, A("DialogRun")),
               T4Stub(A("BaudToIndex"), ret=4, log_regs=("eax",)),
               T4Stub(A("IndexToBaud"), ret=9600, log_regs=("eax",)),
               T4Stub(A("IrqToIndex"), ret=1, log_regs=("eax",)),
               T4Stub(A("IndexToIrq"), ret=7, log_regs=("eax",)),
               T4Stub(0x1d538, log_regs=())])


def test_net_game_start():
    holder = {"r": 0}
    cases = []
    for gs in (0, 1):
        for link in (0, 1):
            for r in (0, 1):
                for pend in (0, 1):
                    for own in (0, 1):
                        def setup(emu, gs=gs, link=link, r=r, pend=pend, own=own):
                            holder["r"] = r
                            holder["link"] = link
                            emu.write(0x593d4, struct.pack("<H", gs))
                            emu.write(0x516ae, struct.pack("<H", pend))
                            emu.write(0x52584, struct.pack("<H", own))
                            emu.write(0x5a8d6, struct.pack("<H", pend))
                            emu.write(0x5a930, struct.pack("<H", 0))
                            emu.write(0x59610, struct.pack("<I", 0))
                        cases.append(T4Case(setup=setup, label="gs=%d link=%d r=%d pend=%d own=%d" % (gs, link, r, pend, own)))

    def link_fn(e, log):
        log()
        return holder["link"]

    t4spec.run_spec(
        os.path.join(SRC, "net_game_start_reference.c"),
        "NetGameStart_", 0x160f0, cases,
        extra={"_cd_1461c": {"addr": 0x1461c},
               "_cd_145f0": {"addr": 0x145f0}},
        out_regs=(),
        watch=[W("setup_state", 1), W("setup_return_state", 1), (0x593d4, 2),
               (0x516ae, 2), W("net_play_flag", 2), (0x593f6, 2),
               W("scenario_race", 2), W("scenario_race_enemy", 2),
               W("evt_pending", 2), W("cheat_flags", 4), (0x59610, 4),
               W("net_error_text", 0x38), W("army_setup", 0x4c),
               W("map_choice_params", 0x2c)],
        stubs=[_dialog_stub(holder, A("DialogRun")),
               T4Stub(A("SetGameMode"), log_regs=("eax",)),
               T4Stub(A("NetLinkStart"), fn=link_fn),
               T4Stub(A("NetLinkExit"), log_regs=()),
               T4Stub(A("FileClose"), log_regs=("eax",))])


def test_setup_menu_loop():
    probe = Emu()
    tbl = []
    base = 0x51718
    for i in range(0x11):
        tbl.append(struct.unpack("<I", probe.read(base + 4 * i, 4))[0])
    ss = A("setup_state")

    def mk_handler(addr):
        def fn(e, log):
            log()
            e.write(ss, b"\x10")
            return None
        return T4Stub(addr, fn=fn)

    handlers = [mk_handler(a) for a in sorted(set(tbl))]
    cases = []
    for pend in (0, 1):
        for music in (0, 1):
            def setup(emu, pend=pend, music=music):
                emu.write(0x516ae, struct.pack("<H", pend))
                emu.write(A("intro_music_started"), struct.pack("<H", music))
                emu.write(0x52584, struct.pack("<H", 2))
                emu.write(ss, b"\x00")
            cases.append(T4Case(setup=setup, label="pend=%d music=%d" % (pend, music)))
    t4spec.run_spec(
        os.path.join(SRC, "setup_menu_loop_reference.c"),
        "SetupMenuLoop_", 0x162b0, cases,
        out_regs=(),
        watch=[W("setup_state", 1), W("setup_return_state", 1), (0x593f6, 2),
               W("intro_music_started", 2), (0x5aba0, 0x10)],
        stubs=[T4Stub(A("DialogArtLoad"), log_regs=()),
               T4Stub(A("DialogArtFree"), log_regs=()),
               T4Stub(A("DialogSoundsLoad"), log_regs=()),
               T4Stub(A("DialogSoundsFree"), log_regs=()),
               T4Stub(A("GdsAlloc"), ret=0x1234, log_regs=("eax",)),
               T4Stub(A("ResourceFreeBody"), log_regs=("eax",)),
               T4Stub(A("MusicStart"), log_regs=("eax",)),
               T4Stub(A("MusicClear"), log_regs=())] + handlers)
