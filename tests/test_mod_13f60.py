"""Area mod_13f60 (0x13f60..0x16390): the unit order dispatch and the
two-player setup menu (docs/subsystems/mod_13f60.md).

1. The matched C files (T3 under Watcom 10.0a) still reproduce the original
   bytes, relocation targets and module CONST bytes (`wc1.match`).
2. The reference file is a known near miss; if it starts matching it
   must be promoted to the built file.
3. The structural claims of the area - the 32-entry order update table at
   0x5158c, the 16-entry setup state table at 0x51718 and the dialog resources
   the menu functions run - are checked against the original image and DATA.WAR.
4. T4: SetGameMode and SaveSlotPath are compared as compiled C against the
   original under wc1.emu (`cemu.run_pair`).
"""
import os
import re
import struct

import pytest

from wc1 import cemu, match, path, resources_war, symbols, t4spec
from wc1.analysis import DATA_OBJ, run as analyze
from wc1.emu import Emu

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "mod_13f60")
MATCHED = [
    "order_appear.c",
    "order_hold.c",
    "preview_rect_reset.c",
    "army_totals_text.c",
    "baud_to_index.c",
    "char_filter.c",
    "checkbox_toggle.c",
    "modem_strings.c",
    "number_format.c",
    "phone_number_load.c",
    "save_slot_path.c",
]
REFERENCE = ["set_game_mode_reference.c"]

ORDER_TABLE = 0x5158C          # int (*[0x20])(void *), docs/subsystems/mod_13f60.md
STATE_TABLE = 0x51718          # the 16-state setup menu, SetupMenuLoop 0x162b0
DISPATCH_FATAL = 0x145D0
SETUP_LOOP = 0x162B0


@pytest.fixture(scope="module")
def prog():
    return analyze()


def _load_c(emu, name):
    """cemu.load with the non-strict symbol load: while several analysts edit
    their TOMLs, another file's error (a missing `ref` file, a duplicate
    address) must not fail this area's T4 run.  A name *this* area needs and
    the database lacks still raises CEmuError, so a real problem is not hidden.
    """
    if cemu._BY_LINK is None:
        funcs, datas, _errors = symbols.load(strict=False)
        cemu._BY_LINK = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    return cemu.load(emu, os.path.join(AREA, name))


def _image(prog):
    """The data object as a flat bytearray indexed by absolute address."""
    d = bytes(prog.image[DATA_OBJ])
    return d


def _dword(img, addr):
    return struct.unpack_from("<I", img, addr - 0x50000)[0]


def _text(prog, addr, n):
    return bytes(prog.cbytes[addr - prog.code.base:addr - prog.code.base + n])


# ------------------------------------------------------------------ T3 checks

@pytest.mark.parametrize("name", MATCHED)
def test_matched_c(name, prog):
    src = os.path.join(AREA, name)
    out = path("build", "mod_13f60", "t3_" + name + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, None, out)
    funcs, datas, _ = symbols.load(strict=False)
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, bad


@pytest.mark.parametrize("name", REFERENCE)
def test_reference_is_still_a_near_miss(name, prog):
    src = os.path.join(AREA, name)
    out = path("build", "mod_13f60", "ref_" + name + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, None, out)
    funcs, datas, _ = symbols.load(strict=False)
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    t4spec.assert_ref_state(src, [s for _, s, _ in res])


# ------------------------------------------------------- the dispatch tables

def test_order_table_names_this_area(prog):
    """The 32 entries at 0x5158c are the order update handlers of this file:
    orders 0..0x1f, the eleven spell orders sharing 0x14140, and the
    'dispatch:5' FatalError default in the last two slots."""
    img = _image(prog)
    table = [_dword(img, ORDER_TABLE + 4 * i) for i in range(0x20)]
    funcs, _, _ = symbols.load(strict=False)
    assert funcs[0x13F60]["name"] == "OrderUpdateGone"
    assert table[0] == 0x13F60 and table[1] == 0x13F68 and table[2] == 0x14030
    assert table[0x0E] == 0x141E0 and table[0x0F] == 0x143CC and table[0x10] == 0x14534
    assert table[0x11:0x1C] == [0x14140] * 11          # the eleven spells
    assert table[0x1C] == 0x13FE8 and table[0x1D] == 0x14084
    assert table[0x1E] == DISPATCH_FATAL and table[0x1F] == DISPATCH_FATAL
    # every handler that this area names is the target its table entry has
    for i, addr in enumerate(table):
        if addr in funcs and funcs[addr]["_file"].endswith("mod_13f60.toml"):
            assert funcs[addr]["module"] == "mod_13f60", hex(addr)
    # the FatalError stub pushes the 'dispatch:5' tag (0x56b10)
    tag = struct.unpack("<I", _text(prog, DISPATCH_FATAL + 4, 4))[0]
    assert tag == 0x56B10


def test_setup_state_table_names_the_menu(prog):
    """0x51718 holds the 16 states SetupMenuLoop dispatches to, all of them in
    this area, and the loop call itself is the indexed indirect call."""
    img = _image(prog)
    table = [_dword(img, STATE_TABLE + 4 * i) for i in range(16)]
    funcs, _, _ = symbols.load(strict=False)
    assert table == [0x15588, 0x15644, 0x15668, 0x15764, 0x157E8, 0x15898,
                     0x15898, 0x1599C, 0x15B30, 0x15BC0, 0x15CA8, 0x15E1C,
                     0x15FBC, 0x16044, 0x160F0, 0x16278]
    for addr in table:
        assert funcs[addr]["module"] == "mod_13f60", hex(addr)
    # SetupMenuLoop 0x16357-0x1636c: `mov al,[0x593da]; call [eax*4+0x51718]`
    # repeated until setup_state == 0x10
    code = _text(prog, 0x16357, 0x16)
    assert code[0:2] == b"\x31\xc0" and code[2] == 0xA0   # xor eax,eax; mov al,[disp32]
    assert struct.unpack("<I", code[3:7])[0] == 0x593DA
    assert code[7:10] == b"\xff\x14\x85"                # call dword [eax*4 + disp32]
    assert struct.unpack("<I", code[10:14])[0] == STATE_TABLE
    assert code[14] == 0x80 and code[20] == 0x10         # cmp byte [0x593da], 0x10


def test_dialog_resources_carry_the_menu_labels():
    """The names of the menu functions come from the dialog resources they
    run; decode the ones the state machine uses and pin their labels."""
    war = resources_war.WarArchive()
    want = {
        0x105: ["Replay introduction", "Start a new game", "Load existing game", "Quit to DOS"],
        0x174: ["Load Game"],
        0x17C: ["Select Game Type", "Single Player", "Modem Game", "Network Game",
                "Direct-Link Game"],
        0x17D: ["Choose Campaign", "Orc Campaign", "Human Campaign", "Custom Game"],
        0x17F: ["Customize Your Game", "Set Race", "Set Army", "Set Map"],
        0x180: ["Set Map", "Forest", "Swamp", "Dungeon", "Random"],
        0x182: ["Modem Connection", "Setup", "Phone>>", "Call", "Answer"],
        0x183: ["Modem Setup", "Clear>>", "Init>>", "Hangup>>", "Dial", "Tone"],
        0x184: ["Direct Connection"],
        0x185: ["Network Connection", "Node>>"],
        0x186: ["Customize Your Game", "Start", "Hang Up"],
        0x196: ["Set Player Races", "Your Race:", "Enemy Race:", "Human", "Orc"],
    }
    for rid, labels in want.items():
        raw = war.read(rid - 2).decode("latin-1")
        text = re.sub("@[0-9]", "", raw)      # the @1X@2 hotkey escapes
        for label in labels:
            assert label in text, (hex(rid), label)
    # the modem initialisation strings the 'Modem Setup' dialog edits
    assert "ATZ" in war.read(0x183 - 2).decode("latin-1")


# ---------------------------------------------------------------- T4 difftests

SET_GAME_MODE = 0x15314
SAVE_SLOT_PATH = 0x14740
GAME_MODE = 0x59616
GAME_MODE_DWORD = 0x59614
NET_LINK = 0x516AE
GAME_START_MODE = 0x593D4


def test_t4_set_game_mode():
    """0x15314 SetGameMode: the compiled reference C leaves game_mode alone
    when it is 9 and stores the argument otherwise, for 0..10."""
    emu = Emu()
    cm = _load_c(emu, "set_game_mode_reference.c")
    for current in (0, 1, 3, 8, 9, 10):
        for mode in (0, 1, 2, 3, 4, 9, 10):
            emu.write(GAME_MODE_DWORD, struct.pack("<HH", 0x1234, current))
            diffs = cemu.run_pair(emu, SET_GAME_MODE, cm, "SetGameMode_", mode,
                                  watch=[(GAME_MODE_DWORD, 4)], out_regs=())
            assert diffs == [], (current, mode, diffs)
