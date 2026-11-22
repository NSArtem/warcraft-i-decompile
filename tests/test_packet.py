"""PACKET.C area 0x214b0..0x21cf0 (analysis/symbols/packet.toml,
docs/subsystems/packet.md).

Kinds of test here:
  * structural: every discovered function start of the range is in the symbol
    database with module PACKET.C, the dispatch jump table at 0x215a8 holds
    the documented case addresses, and the module's string pool is where the
    fatal messages are;
  * T3 re-check: the 20 byte-matched files stay MATCH under wc1.match
    (Watcom 10.0a, OPT flags);
  * reference guard: the three near-miss files must still NOT match;
  * claim difftests of the documented framing (the send path
    sender -> fn_214d4 -> NetSendDataMessage -> net_msg, the id stamping and
    the no-link loopback through NetRecvDataMessage);
  * T4 difftests: the compiled reference C against the original under
    wc1.cemu.run_pair (stubs recorded for both runs).
"""
import os
import struct

import pytest

from wc1 import analysis, cemu, codegen_sweep, match, path, symbols, t4spec

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "packet")
LO, HI = 0x214B0, 0x21CF0
FLAGS = "-s -ot -ol -4r -zp2"

# link name -> built file (T3 under Watcom 10.0a)
MATCHED = {
    "PacketGenerateId_": "packet_generate_id.c",
    "fn_214d4_": "packet_send.c",
    "PacketSendIdle_": "net_send_idle.c",
    "PacketCheckSync_": "packet_check_sync.c",
    "PacketTick_": "packet_tick.c",
    "NetSendTargetMode_": "net_send_target_mode.c",
    "NetSendTargetCancel_": "net_send_target_cancel.c",
    "NetSendOrder_": "net_send_order.c",
    "NetSendPlaceStart_": "net_send_place_start.c",
    "PlaceBoxPress_": "place_box_press.c",
    "NetSendPlaceConfirm_": "net_send_place_confirm.c",
    "NetSendCancelConstruction_": "net_send_cancel_construction.c",
    "NetSendStartResearch_": "net_send_start_research.c",
    "NetSendStartTraining_": "net_send_start_training.c",
    "NetSendCancelProduction_": "net_send_cancel_production.c",
    "NetSendControlPacket_": "net_send_control_packet.c",
    "NetSendCheatFlags_": "net_send_cheat_flags.c",
    "NetSendChatText_": "net_send_chat_text.c",
    "ResetPacketId_": "reset_packet_id.c",
    "NetResetPacketId_": "net_reset_packet_id.c",
}
REF = {
    "PacketDispatch_": "packet_dispatch_reference.c",
    "NetSendSelection_": "net_send_selection_reference.c",
}
# NetSendSyncMessage (0x21cb8) is named and its reference C is owned by the
# neighbouring mod_20c30 area (src/mod_20c30/net_send_sync_message_reference.c,
# ref = that path in mod_20c30.toml); this area difftests the same file.
SYNC_REF = path("src", "mod_20c30", "net_send_sync_message_reference.c")
# the only placeholder name the range still carries: fn_214d4 sits in
# mod_20c30.toml (the neighbouring area needed the send entry as a callee);
# renaming it PacketSend is a change request to the build owner.
PLACEHOLDER = {"fn_214d4_"}

# addresses used below (evidence in packet.toml / the other areas' TOMLs)
PACKET_ID = 0x52B00
PACKET_SYNC_ERROR = 0x52B02
PENDING_ORDER = 0x5A7C4
NET_PLAY = 0x52586
DIALOG_ENABLED = 0x517CC
OWN_CAMPAIGN = 0x52584
NET_EVENT_PENDING = 0x5A11A
NET_MSG = 0x5A000
NET_SYNC_STATE = 0x5310C
RNG_STATE = 0x50D7C
JUMP_TABLE = 0x215A8
SEND_ENTRY = 0x214D4
REF_RELOCATE = 0x248E0
LOCK_ADJUST = 0x29424
UNIT_CANCEL_PRODUCTION = 0x116A8
UNIT_ARRAY_VAR = 0x59640


def program():
    return codegen_sweep.program()


def by_link():
    funcs, datas, _ = symbols.load()
    return funcs, datas, {e["link_name"]: e for t in (funcs, datas) for e in t.values()}


def flags(src):
    full = match.file_cflags(path(src))
    assert full.startswith(match.BASE_CFLAGS + " "), full
    return full


def _u16(emu, a):
    return struct.unpack("<H", emu.read(a, 2))[0]


def _put16(emu, a, v):
    emu.write(a, struct.pack("<H", v))


# ---------------------------------------------------------------- structure

def test_every_start_is_in_the_database():
    """All 23 function starts of the module are named with module PACKET.C."""
    funcs, _datas, _ = by_link()
    starts = [f["start"] for f in program().functions if LO <= f["start"] < HI]
    assert len(starts) == 23, [hex(a) for a in starts]
    missing = [hex(a) for a in starts if a not in funcs]
    assert not missing, missing
    wrong = [(hex(a), funcs[a]["module"]) for a in starts if funcs[a]["module"] != "PACKET.C"]
    assert not wrong, wrong


def test_only_the_documented_placeholder_is_left():
    """fn_214d4 (mod_20c30.toml) is the one placeholder the range may still
    carry (rename to PacketSend requested); no new one may appear."""
    funcs, _datas, _ = by_link()
    placeholders = {funcs[a]["link_name"] for a in funcs
                    if LO <= a < HI and funcs[a]["name"].startswith("fn_")}
    assert placeholders <= PLACEHOLDER, placeholders


def test_dispatch_jump_table_matches_the_documented_types():
    """cd_215a8 (18 dwords at 0x215a8) maps packet type -> case address:
    0..2 no-op, 3 selection, 4 place start, 5 place cancel, 6 place confirm,
    7/8 target mode, 9 order, 0xa cancel construction, 0xb/0xc/0xd
    research/training/cancel production, 0xe control, 0xf chat,
    0x10 cheat flags, 0x11 sync block."""
    p = program()
    want = [0x21839, 0x21839, 0x21839, 0x21613, 0x21674, 0x2168e, 0x2165c,
            0x216a3, 0x216b8, 0x216cd, 0x2175f, 0x21787, 0x217ab, 0x217cf,
            0x217ee, 0x21802, 0x21823, 0x21834]
    got = [p.fix_at[JUMP_TABLE + 4 * i][1] for i in range(18)]
    assert got == want, [hex(a) for a in got]


def test_module_strings():
    """The three fatal/notice strings sit in the module's own CONST slice."""
    img = bytes(program().data.data)
    base = program().data.base

    def text(a):
        end = img.index(b"\0", a - base)
        return img[a - base:end].decode("ascii")

    assert text(0x57278) == "A syncing error occurred during gameplay"
    assert text(0x572A4) == "pktunit: %d %d"
    assert text(0x572B4) == "PKT:7 %d %d"
    assert text(0x572C0) == "message sent to opponent"


# ---------------------------------------------------------------- T3

def test_t3_matched_c():
    """Every built file compiles byte-identically (code, relocations, module
    data) under the compiler its header declares."""
    _funcs, _datas, links = by_link()
    seen = []
    for link, name in sorted(MATCHED.items()):
        src = path(AREA, name)
        out = path("build", "packet", "t3_" + name[:-2] + ".obj")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        mod = match.compile_c(src, flags(src), out)
        res = match.match_module(program(), mod, links)
        bad = [(n, s, pr) for n, s, pr in res if s != "MATCH"]
        assert not bad, (name, bad)
        seen += [n for n, _, _ in res if not n.startswith("[")]
    assert sorted(seen) == sorted(MATCHED), sorted(seen)


def test_reference_c_stays_a_near_miss():
    """The reference files model the logic but are not byte-matches; if one
    starts matching it has to be promoted (verified + src = ...)."""
    for link, name in sorted(REF.items()):
        src = path(AREA, name)
        if t4spec.t3_promoted(src):  # promoted: its own codegen-compiler/-flags header applies
            t4spec.assert_ref_state(src, t4spec.ref_statuses(src), name)
            continue
        _, rows, err = codegen_sweep.sweep(src, [FLAGS + ""], quiet=True)[0]
        assert rows is not None, err
        assert [r for r in rows if r[0] + "_" == link], (name, rows)
        t4spec.assert_ref_state(src, [r[2] for r in rows])


# ---------------------------------------------------------------- wiring

def test_headers_declare_10_0a_and_opt():
    for name in sorted(set(MATCHED.values()) | set(REF.values())):
        head = open(path(AREA, name), errors="replace").read(400)
        assert "codegen-compiler: 10.0a" in head, name
        assert "codegen-flags: -s -ot -ol -4r -zp2" in head, name


def test_src_and_ref_entries_are_the_areas_files():
    """This area reports its matched files instead of wiring src = itself; once
    the owner wires them, every src/ref of the range must be one of them (so a
    renamed or moved file is caught here)."""
    funcs, _datas, _ = by_link()
    srcs = {os.path.join("src", "packet", f) for f in MATCHED.values()}
    refs = {os.path.join("src", "packet", f) for f in REF.values()}
    refs.add(os.path.relpath(SYNC_REF, path()).replace(os.sep, "/"))
    for a, e in funcs.items():
        if not LO <= a < HI:
            continue
        if e.get("src"):
            assert e["src"] in srcs, (hex(a), e["name"], e["src"])
        if e.get("ref"):
            assert e["ref"] in refs, (hex(a), e["name"], e["ref"])


# ---------------------------------------------------------------- framing
# The send path is tested end to end with the real fn_214d4 and
# NetSendDataMessage: without a link they fill the static net_msg buffer
# (0x5a000), which is the two-player-independent "loopback" the receive side
# reads back (docs/subsystems/packet.md section 2).

def emu_mod():
    from wc1.emu import Emu
    return Emu()


def _send(emu, addr, *args, watch=()):
    """Call a sender in single-player mode and return (net_msg, size-byte)."""
    _put16(emu, NET_SYNC_STATE, 0)          # no link: static loopback
    _put16(emu, PACKET_ID, 0x1234)
    emu.write(NET_MSG, b"\xee" * 0x10)
    emu.call(addr, *args)
    msg = emu.read(NET_MSG, 0x10)
    return msg, _u16(emu, PACKET_ID)


SENDERS = [
    # addr, args, type byte, payload length (packet body after the 4-byte id)
    (0x21980, (), 0x07, 0),          # NetSendTargetMode
    (0x219AC, (), 0x08, 0),          # NetSendTargetCancel
    (0x21AC8, (0x20,), 0x04, 1),     # NetSendPlaceStart(farm)
    (0x21AF8, (0,), 0x05, 0),        # PlaceBoxPress
    (0x21BF4, (), 0x0D, 0),          # NetSendCancelProduction
    (0x21B94, (6,), 0x0B, 1),        # NetSendStartResearch(row 6)
    (0x21BC4, (8,), 0x0C, 1),        # NetSendStartTraining(archer)
    (0x21C20, (8,), 0x0E, 2),        # NetSendControlPacket(menu)
]


@pytest.mark.parametrize("addr,args,type_byte,plen", SENDERS)
def test_sender_framing(addr, args, type_byte, plen):
    """A sender produces one link message: size = body+4, link type 4, the
    packet type at +4, the sync id stamped at +5 (and packet_id cleared)."""
    emu = emu_mod()
    msg, pid = _send(emu, addr, *args)
    assert msg[1] == 4, msg.hex()                    # link data message
    assert msg[0] == 4 + 3 + plen, msg.hex()         # size = header + body
    assert msg[4] == type_byte, msg.hex()
    assert struct.unpack("<H", msg[5:7])[0] == 0x1234, msg.hex()
    assert pid == 0, "the id is consumed by the packet it was stamped on"


def test_sender_payloads():
    """The type-specific payload words."""
    emu = emu_mod()
    msg, _ = _send(emu, 0x21AC8, 0x21)               # PlaceStart 0x21
    assert msg[7] == 0x21
    msg, _ = _send(emu, 0x21BC4, 0x08)               # StartTraining 8
    assert msg[7] == 0x08
    msg, _ = _send(emu, 0x21C20, 0x000C)             # ControlPacket 0xc
    assert struct.unpack("<H", msg[7:9])[0] == 0x000C
    msg, _ = _send(emu, 0x21C44, 0x00A5B6C7)         # CheatFlags dword
    assert msg[0] == 11 and struct.unpack("<I", msg[7:11])[0] == 0x00A5B6C7
    msg, _ = _send(emu, 0x21B24, 0x00120034)         # PlaceConfirm cell
    assert msg[0] == 11 and struct.unpack("<I", msg[7:11])[0] == 0x00120034


def test_cheat_flags_and_chat_skip_the_panel_lock():
    """fn_214d4 takes no lock; the command-card senders do (StatusPanelLockAdjust(1)).
    NetSendCheatFlags and NetSendChatText are the two that do not."""
    emu = emu_mod()
    locks = []
    emu.stubs[LOCK_ADJUST] = lambda e: locks.append(e.reg("eax") & 0xFFFF) or 0
    _send(emu, 0x21C44, 0x1)
    assert locks == []
    _send(emu, 0x21B94, 1)                            # research: takes the lock
    assert locks == [1]


def test_chat_text_payload_and_notice():
    """NetSendChatText copies the NUL-terminated text and shows the notice."""
    emu = emu_mod()
    notices = []
    emu.stubs[0x19F70] = lambda e: notices.append(e.reg("eax")) or 0
    _put16(emu, NET_PLAY, 1)
    text = emu.alloc(0x20)
    emu.write(text, b"hello\0")
    msg, _ = _send(emu, 0x21C68, text, 5)
    assert msg[0] == 4 + 3 + 6                       # header + text + NUL
    assert msg[7:13] == b"hello\0", msg.hex()
    assert notices == [0x572C0], [hex(a) for a in notices]


def test_chat_needs_two_player():
    emu = emu_mod()
    _put16(emu, NET_PLAY, 0)
    text = emu.alloc(0x20)
    emu.write(text, b"hi\0")
    _put16(emu, NET_SYNC_STATE, 0)
    emu.write(NET_MSG, b"\xee" * 0x10)
    emu.call(0x21C68, text, 2)
    assert emu.read(NET_MSG, 1) == b"\xee"           # nothing was sent


def test_idle_packet_and_empty_message():
    """PacketSendIdle: with a running two-player game it sends the 3-byte
    type-1 packet (which carries the id), otherwise the empty message."""
    emu = emu_mod()
    _put16(emu, NET_PLAY, 1)
    _put16(emu, DIALOG_ENABLED, 1)
    _put16(emu, 0x516AE, 1)                          # link mode: no pacing 0
    _put16(emu, PACKET_ID, 0x2222)
    emu.write(NET_MSG, b"\xee" * 0x10)
    emu.call(0x2150C)
    msg = emu.read(NET_MSG, 0x10)
    assert msg[0] == 7 and msg[1] == 4 and msg[4:7] == b"\x01\x22\x22", msg.hex()
    assert _u16(emu, PACKET_ID) == 0
    _put16(emu, NET_PLAY, 0)
    emu.write(NET_MSG, b"\xee" * 0x10)
    emu.call(0x2150C)
    msg = emu.read(NET_MSG, 0x10)
    assert msg[:2] == b"\x04\x01", msg.hex()          # size 4, link type 1


def test_sync_id_is_the_folded_rng_state():
    """PacketGenerateId: id = (state ^ state>>16) & 0xffff, 1 when zero."""
    emu = emu_mod()
    for state in (0, 1, 0x12345678, 0x00010001, 0xFFFF0000, 0xDEADBEEF, 0x0000FFFF):
        emu.write(RNG_STATE, struct.pack("<I", state))
        _put16(emu, PACKET_ID, 0x7777)
        emu.call(0x214B0)
        want = ((state >> 16) ^ state) & 0xFFFF or 1
        assert _u16(emu, PACKET_ID) == want, hex(state)


def test_sync_check_latches():
    """PacketCheckSync fatal path: only two non-empty packets with different
    non-zero ids report; the flag latches so the message appears once."""
    emu = emu_mod()
    fatal = []
    emu.stubs[0x30BF0] = lambda e: fatal.append(e.u32(e.reg("esp") + 4)) or 0
    a = emu.alloc(0x20)
    b = emu.alloc(0x20)

    def run(pa, pb, play=1, latch=0):
        emu.write(a, bytes(pa))
        emu.write(b, bytes(pb))
        _put16(emu, NET_PLAY, play)
        _put16(emu, PACKET_SYNC_ERROR, latch)
        emu.call(0x21554, a, b)
        return _u16(emu, PACKET_SYNC_ERROR)

    assert run(b"\x07\x34\x12", b"\x07\x34\x12") == 0          # equal ids
    assert run(b"\x07\x00\x00", b"\x07\x11\x11") == 0          # zero id
    assert run(b"\x00\x00\x00", b"\x07\x11\x11") == 0          # empty packet
    assert run(b"\x07\x34\x12", b"\x07\x35\x12", play=0) == 0  # single player
    assert run(b"\x07\x34\x12", b"\x07\x35\x12", latch=1) == 1  # already latched
    assert run(b"\x07\x34\x12", b"\x07\x35\x12") == 1 and fatal == [0x57278]


# ---------------------------------------------------------------- T4

def _load(emu, name):
    return cemu.load(emu, path(AREA, name))


def test_t4_net_send_selection():
    """0x219d8 (reference C): identical packet for the same selection list."""
    emu = emu_mod()
    cm = _load(emu, REF["NetSendSelection_"])
    packets = []

    def send_entry(e):
        n = e.reg("eax") & 0xFFFF
        p = e.reg("edx")
        if n >= 3:                       # what fn_214d4 does: stamp the id
            emu.write(p + 1, b"\xbb\xaa")
        packets.append((n, emu.read(p, n)))

    def relocate(e):
        return (e.reg("eax") * 3 + e.reg("ebx") + 7) & 0xFFFF

    emu.stubs[SEND_ENTRY] = send_entry
    emu.stubs[REF_RELOCATE] = relocate
    emu.stubs[LOCK_ADJUST] = lambda e: 0
    units = emu.alloc(0x40)
    for count in (0, 1, 2, 3, 4):
        for k in range(4):
            emu.put_u32(units + 4 * k, 0x1000 + k)
        packets.clear()
        diffs = cemu.run_pair(emu, 0x219D8, cm, "NetSendSelection_", count, units,
                              watch=[(PENDING_ORDER, 2)], out_regs=())
        assert diffs == [], (count, diffs)
        assert len(packets) == 2, packets
        assert packets[0] == packets[1], packets
        n, body = packets[0]
        assert n == 5 + 2 * count, (n, count)
        assert body[0] == 3
        assert struct.unpack("<H", body[3:5])[0] == count


def test_t4_net_send_sync_message():
    """0x21cb8 (reference C): the same 0x15-byte packet carrying the block."""
    emu = emu_mod()
    cm = cemu.load(emu, SYNC_REF)
    packets = []
    def send_entry(e):
        n = e.reg("eax") & 0xFFFF
        p = e.reg("edx")
        if n >= 3:
            emu.write(p + 1, b"\xbb\xaa")
        packets.append((n, emu.read(p, n)))

    emu.stubs[SEND_ENTRY] = send_entry
    block = emu.alloc(0x20)
    for k in range(0x12):
        emu.write(block + k, bytes([0x40 + k]))
    diffs = cemu.run_pair(emu, 0x21CB8, cm, "NetSendSyncMessage_", block,
                          watch=[(PACKET_ID, 2)], out_regs=())
    assert diffs == [], diffs
    assert len(packets) == 2
    assert packets[0] == packets[1], packets
    n, body = packets[0]
    assert n == 0x15
    assert body[0] == 0x11
    assert body[3:0x12 + 3] == bytes(range(0x40, 0x40 + 0x12))


def _dispatch_stubs(emu, calls):
    """Record every executor the dispatcher calls (both runs, back to back)."""
    def rec(tag, *regs):
        def f(e):
            calls.append((tag,) + tuple(e.reg(r) for r in regs))
            return 0
        return f

    emu.stubs[LOCK_ADJUST] = rec("lock", "eax")
    emu.stubs[0x25F9C] = rec("selection", "eax", "edx")
    emu.stubs[0x260C8] = rec("order", "eax", "edx", "ebx", "ecx")
    emu.stubs[0x2B31C] = rec("target_on")
    emu.stubs[0x2B390] = rec("target_off")
    emu.stubs[0x2E384] = rec("cancel_building", "eax")
    emu.stubs[0x19C14] = rec("menu", "eax")
    emu.stubs[0x19EDC] = rec("chat", "eax", "edx", "ebx")
    emu.stubs[0x22798] = rec("place_start", "eax")
    emu.stubs[0x22930] = rec("place_cancel")
    emu.stubs[0x22AE4] = rec("place_confirm", "eax")
    emu.stubs[0x25CC4] = lambda e: 0x5C000
    emu.stubs[0x11538] = rec("research", "eax", "edx")
    emu.stubs[0x115F4] = rec("training", "eax", "edx")
    emu.stubs[UNIT_CANCEL_PRODUCTION] = rec("cancel_production", "eax")
    emu.stubs[0x1284C] = rec("cheat", "eax")
    emu.stubs[0x2445C] = rec("sync_block", "eax")
    emu.stubs[0x30BF0] = lambda e: calls.append(
        ("fatal", e.u32(e.reg("esp") + 4))) or 0
    emu.stubs[REF_RELOCATE] = lambda e: 0x5C100


def test_t4_packet_dispatch():
    """0x215f0 (reference C): every packet type runs the same executors with
    the same arguments as the original."""
    emu = emu_mod()
    cm = _load(emu, REF["PacketDispatch_"])
    calls = []
    _dispatch_stubs(emu, calls)
    buf = emu.alloc(0x20)
    units = [0x1234, 0x2345, 0x3456, 0x4567]
    # pending order 3 is in order_handlers (0x20eb4), so no fatal path
    _put16(emu, PENDING_ORDER, 0)
    for ptype in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF,
                  0x10, 0x11, 0x12):
        for count in ((0, 1, 4) if ptype == 3 else (0,)):
            body = bytearray(0x20)
            body[0] = ptype
            if ptype == 3:
                struct.pack_into("<H", body, 3, count)
                for k in range(count):
                    struct.pack_into("<H", body, 5 + 2 * k, units[k])
            elif ptype == 9:
                struct.pack_into("<H", body, 3, 5)          # x
                struct.pack_into("<H", body, 5, 6)          # y
                struct.pack_into("<H", body, 7, 0x1234)     # unit index
                struct.pack_into("<H", body, 9, 3)          # order: move
            elif ptype == 0xA:
                struct.pack_into("<H", body, 3, 0x1234)
            elif ptype in (4, 0xB, 0xC):
                body[3] = 0x20
            elif ptype in (6, 0x10):
                struct.pack_into("<I", body, 3, 0x00120034)
            elif ptype == 0xE:
                struct.pack_into("<H", body, 3, 8)
            elif ptype == 0xF:
                body[3:9] = b"hello\0"
            emu.write(buf, bytes(body))
            _put16(emu, NET_EVENT_PENDING, 0)
            calls.clear()
            diffs = cemu.run_pair(emu, 0x215F0, cm, "PacketDispatch_", buf,
                                  watch=[(PENDING_ORDER, 2),
                                         (0x5A7C0, 2)], out_regs=())
            assert diffs == [], (ptype, count, diffs)
            half = len(calls) // 2
            assert calls[:half] == calls[half:], (ptype, count, calls)


def test_t4_packet_tick_loopback():
    """0x21844 (T3, but the tick is the only caller of the two receive calls;
    the C is exercised through the shared static loopback): a command queued
    in net_msg is dispatched on the next tick."""
    emu = emu_mod()
    cm = cemu.load(emu, path(AREA, "packet_tick.c"))
    seen = []
    emu.stubs[0x215F0] = lambda e: seen.append(emu.read(e.reg("eax"), 4)) or 0
    emu.stubs[0x214B0] = lambda e: 0
    emu.stubs[0x2150C] = lambda e: 0
    emu.stubs[0x21554] = lambda e: 0
    _put16(emu, NET_PLAY, 0)
    _put16(emu, OWN_CAMPAIGN, 1)
    # a queued type-7 command packet: net_msg = 7 | 4 | seq | type id
    emu.write(NET_MSG, bytes([7, 4, 0, 0, 7, 0x34, 0x12]))
    diffs = cemu.run_pair(emu, 0x21844, cm, "PacketTick_",
                          watch=[(NET_MSG, 0x10), (0x51E24, 2)], out_regs=())
    assert diffs == [], diffs
    assert len(seen) == 2 and seen[0] == seen[1], seen
    assert seen[0][0] == 7


def test_no_link_loopback_receive():
    """The documented single-player loopback: NetRecvDataMessage reads the
    static net_msg payload and clears it (claim check of the framing)."""
    emu = emu_mod()
    _put16(emu, NET_SYNC_STATE, 0)
    emu.write(NET_MSG, bytes([8, 4, 0, 0, 9, 0x34, 0x12, 1, 2]))
    dst = emu.alloc(0x90)
    ok = emu.call(0x247D0, 0, dst)
    assert ok == 1
    assert emu.read(dst, 4) == bytes([9, 0x34, 0x12, 1])
    assert emu.read(NET_MSG, 0x80) == bytes(0x80), "the message is consumed"
