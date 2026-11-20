import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src', 'save')
_FUNCS, _DATAS = t4spec.load_lenient()
_F = {e["name"]: a for a, e in _FUNCS.items()}
_D = {e["name"]: a for a, e in _DATAS.items()}


def F(name):
    return _F[name]


def D(name):
    return _D[name]


_BUF = {}


def _init_handshake(emu):
    # reply buffer allocated inside init_emu so it never overlaps the C module
    _BUF["reply"] = emu.alloc(32, 16)


def _p16(v):
    return struct.pack("<H", v & 0xFFFF)


def _p32(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


def _memcpy_stub(e, log):
    dst, src, n = e.reg("eax"), e.reg("edx"), e.reg("ebx")
    e.write(dst, e.read(src, n))
    log(n)
    return dst


def test_t3_files():
    t4spec.assert_t3_matches(SRC, [])


def test_ref_guard():
    t4spec.assert_ref_mismatch(SRC, ['net_link_handshake_reference.c', 'net_link_start_reference.c', 'net_load_sync_message_reference.c'])


def test_net_link_start():
    stubs_for = lambda r: [
        T4Stub(0x20a80, ret=r, log_regs=()),
        T4Stub(F("atexit"), log_regs=("eax",)),
    ]
    for r in (0, 1, 5, 0x10000, 0xFFFF):
        t4spec.run_spec(
            os.path.join(SRC, "net_link_start_reference.c"), "NetLinkStart_", 0x23ec0,
            [T4Case(label="ret=%#x" % r)],
            stubs=stubs_for(r), out_regs=("eax",))


def _hs_case(label, campaign_own, cd, ok12, rep_campaign, rep_now, rep_ver,
             rep_cd, rep_side=0x33, link_speed=0x11):
    reply = (bytes([0x10, 2]) + _p16(0) + _p32(0x4444) + _p32(rep_now)
             + bytes([rep_campaign, rep_cd, rep_ver, rep_side]))

    def setup(emu):
        emu.write(_BUF["reply"], reply)
    mem = {
        D("own_campaign"): _p16(campaign_own),
        D("cd_present"): bytes([cd]),
        D("net_link_speed"): _p16(link_speed),
        D("prefs_block"): _p32(0x1234) + b"\0" * 16,
        0x5a8d6: _p16(0),
        0x5a90e: _p16(0),
        0x5a9b6: _p16(0),
    }
    return T4Case(label=label, mem=mem, setup=setup)


def test_net_link_handshake():
    def poll(e, log):
        log(e.reg("eax"))
        e.write(e.reg("edx"), _p32(_BUF["reply"]))
        return 0

    def mk(ok):
        return [
            T4Stub(F("fn_20b2c") if "fn_20b2c" in _F else 0x20b2c, ret=ok, log_regs=()),
            T4Stub(F("NetResetLink"), log_regs=()),
            T4Stub(F("NetSendMessage"), log_regs=("eax",)),
            T4Stub(F("VersionMismatchDialog"), log_regs=()),
            T4Stub(F("ShowMessage"), log_regs=("eax", "edx", "ebx")),
            T4Stub(F("delay"), log_regs=("eax",)),
            T4Stub(F("memcpy"), fn=_memcpy_stub),
            T4Stub(F("time"), ret=1000, log_regs=()),
            T4Stub(0x12f24, fn=poll),
            T4Stub(0x19470, log_regs=("eax",)),
        ]
    watch = [(D("net_msg"), 0x10), (D("net_enemy_record"), 12),
             (D("prefs_block"), 20), (D("own_campaign"), 2),
             (D("cd_present"), 1), (D("net_link_speed"), 2),
             (D("net_sync_state"), 4), (D("screen_mode"), 2)]
    src = os.path.join(SRC, "net_link_handshake_reference.c")
    # link init fails
    t4spec.run_spec(src, "NetLinkHandshake_", 0x23edc,
                    [_hs_case("link fail", 0, 1, 0, 1, 900, 0x25, 1)],
                    watch=watch, stubs=mk(0), init_emu=_init_handshake)
    cases = [
        _hs_case("version mismatch", 0, 1, 1, 1, 900, 0x24, 1),
        _hs_case("bad type-free diff campaign", 0, 1, 1, 1, 900, 0x25, 1),
        _hs_case("same campaign we older", 0, 1, 1, 0, 2000, 0x25, 1),
        _hs_case("same campaign we newer", 0, 1, 1, 0, 500, 0x25, 1),
        _hs_case("own1 same", 1, 1, 1, 1, 500, 0x25, 0),
        _hs_case("own1 newer remote", 1, 1, 1, 1, 5000, 0x25, 1),
        _hs_case("no cd anywhere", 0, 0, 1, 1, 900, 0x25, 0),
        _hs_case("cd from remote", 0, 0, 1, 1, 900, 0x25, 1),
        _hs_case("own0 remote prefs", 0, 1, 1, 1, 900, 0x25, 1, 0x77, 0x22),
    ]
    t4spec.run_spec(src, "NetLinkHandshake_", 0x23edc, cases,
                    watch=watch, stubs=mk(1), init_emu=_init_handshake)


def _sync_state(reply, st_hi=0, pending=1, now=500, camp=1, side=3,
                cnt=100, cnt_o=100):
    mem = {
        D("net_event_pending"): _p16(pending),
        D("net_sync_state"): _p16(0) + _p16(st_hi),
        D("net_sync_reply"): _p16(reply),
        D("net_sync_msg"): (_p32(0x99) + _p32(now) + bytes([camp, 1, 0x25, side])
                            + _p16(cnt) + _p16(cnt_o)),
        D("screen_mode"): _p16(7),
        D("game_mode"): _p16(0),
        D("net_load_state"): b"\x09",
        D("evt_pending"): _p16(5),
        D("net_send_slot"): _p16(2),
        D("net_send_state"): _p16(1) + _p16(3) + _p16(4),
    }
    return mem


def _msg(now=500, camp=0, side=3, cnt=100, cnt_o=100):
    return (_p32(0x77) + _p32(now) + bytes([camp, 1, 0x25, side])
            + _p16(cnt) + _p16(cnt_o))


def test_net_load_sync_message():
    msg_addr = D("net_send_ring") + 0x500

    def case(label, msg, **kw):
        mem = _sync_state(**kw)
        mem[msg_addr] = msg
        return T4Case(label=label, args=(msg_addr,), mem=mem)

    cases = [
        case("not pending", _msg(), reply=1, pending=0),
        case("state==2", _msg(), reply=1, st_hi=2),
        case("reply 0", _msg(), reply=0),
        case("match", _msg(), reply=1),
        case("match last slot", _msg(), reply=1),
        case("now differs", _msg(now=501), reply=1),
        case("same campaign", _msg(camp=1), reply=1),
        case("side differs", _msg(side=4), reply=1),
        case("cnt_other low", _msg(cnt_o=80), reply=1),
        case("cnt_other edge", _msg(cnt_o=90), reply=1),
        case("cnt_other high", _msg(cnt_o=101), reply=1),
        case("peer cnt out", _msg(cnt=120), reply=1),
        case("peer cnt edge", _msg(cnt=110), reply=1),
    ]
    stubs = [
        T4Stub(F("NetResetLink"), log_regs=()),
        T4Stub(F("ShowMessage"), log_regs=("eax", "edx", "ebx")),
        T4Stub(0x20a50, log_regs=("edx",)),
        T4Stub(F("ResetPacketId"), log_regs=()),
        T4Stub(F("SaveReadStream"), ret=0x1234, log_regs=("ebx", "edx")),
        T4Stub(F("memcpy"), fn=_memcpy_stub),
        T4Stub(0x24304, log_regs=()),
    ]
    names = [("net_event_pending", 2), ("net_sync_state", 4), ("net_sync_reply", 2),
             ("net_sync_msg", 18), ("screen_mode", 2), ("game_mode", 2),
             ("net_load_state", 1), ("evt_pending", 2), ("net_send_slot", 2),
             ("net_send_state", 6), ("net_enemy_record", 12),
             ("net_stream_pos", 4), ("net_link_speed", 2),
             ("net_ring_state", 4)]
    watch = [(D(n), s) for n, s in names]
    t4spec.run_spec(os.path.join(SRC, "net_load_sync_message_reference.c"),
                    "NetLoadSyncMessage_", 0x2445c, cases,
                    watch=watch, stubs=stubs, out_regs=())
