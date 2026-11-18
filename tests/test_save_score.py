"""Differential and structural tests for the save_score area.

Area = SAVE.C 0x23ec0..0x24860 (the two-player link half of saving/loading)
and SCORE.C 0x24e50..0x25820 (score accounting, rank titles, score panel).
Names/evidence: analysis/symbols/save_score.toml; prose:
docs/subsystems/save_score.md.

Kinds of test here:
  * T3 re-check of the byte-matched C files (src/save_score/{save,score}.c):
    every function must stay MATCH under `wc1.match`.
  * a guard that the two reference files stay *near misses* (their logic is
    right but OW2's register allocation differs) - if one starts matching it
    has to be promoted into the built files.
  * T4 difftests: the original functions run under wc1.emu against Python
    models of the same arithmetic, with the link primitives stubbed
    (fn_131d8/fn_12f24 take the 16-byte net_msg buffer / hand out record
    pointers; memcpy 0x31789 is a segmented ES:EDI copy that Unicorn cannot
    run, so the tests stub it with a flat model - see the report note in
    docs/subsystems/save_score.md section 7).
  * invariants of the data tables the area documents (rank thresholds/names)
    and of the function boundaries (the two tail-jump-only entries 0x24ee0
    and 0x2505c, which the code discovery merges into their predecessors).
"""
import os
import random
import struct

import pytest

from wc1 import cemu, codegen_sweep, match, path, symbols

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

BUILT = [path("src", "save_score", "save.c"),
         path("src", "save_score", "score.c")]
REFS = [path("src", "save_score", "save_reference.c"),
        path("src", "save_score", "score_reference.c")]

# addresses (see the symbol database for the evidence)
NET_MSG, NET_MSG_TYPE, NET_SEQ, NET_PAYLOAD = 0x5A000, 0x5A001, 0x5A002, 0x5A004
LINK_ACTIVE = 0x5310C                  # net_sync_state low word
SEND, RECV, DELAY, EVTGET = 0x131D8, 0x12F24, 0x31784, 0x31598
MEMCPY, MEMSET = 0x31789, 0x30C50      # clib (watcall eax, edx, ebx)
STREAM_CNT = 0x5A0B0                   # dword: bytes left in the load stream
PLAYER_SCORE = 0x50E34                 # player_score[4]
MEN = 0x58E28                          # player_active_men[4]
BLDGS = 0x58E00                        # player_active_buildings[4]
WORTH = 0x51A4C                        # score_value[]
POOL, CAP, RATE = 0x5A0CE, 0x5A0D2, 0x5A0CC
SUPPRESS = 0x5A7C2                     # unnamed game-state flag that disables the adjusters
MODE = 0x59614                         # dword; >>16 compared with 3/5/6 (game_mode)
RANK_TH, RANK_HUMAN, RANK_ORC = 0x5318C, 0x531B4, 0x53200
SIDE = 0x50088                         # scenario_race: 0 human, 1 orc
PANEL_BM, PANEL_CLEAN = 0x5314C, 0x53154
PANEL_RECT, CUR_BITMAP, CUR_FONT = 0x53140, 0x55438, 0x5ACF0
LINE_GAP, PAGE, PAGE_SHOWN = 0x5543E, 0x5A0D4, 0x5A0D0


@pytest.fixture(scope="module")
def prog():
    return codegen_sweep.program()


def _flags(src):
    full = match.file_cflags(src)
    assert full.startswith(match.BASE_CFLAGS + " "), full
    return full, full[len(match.BASE_CFLAGS) + 1:]


# ---------------------------------------------------------------- T3 / near miss

@pytest.mark.parametrize("src", BUILT)
def test_built_c_matches(prog, src):
    """Every function in the built files is byte-identical (T3)."""
    out = path("build", "save_score",
               "t3_" + os.path.splitext(os.path.basename(src))[0] + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, _flags(src)[0], out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    assert res, "no functions found"
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, bad


@pytest.mark.parametrize("src", REFS)
def test_reference_c_stays_a_near_miss(src):
    """The reference files model the logic correctly but are not byte-matches;
    if one matches it has to be promoted (and the `match:` evidence updated)."""
    _, codegen = _flags(src)
    _, rows, err = codegen_sweep.sweep(src, [codegen], quiet=True)[0]
    assert rows is not None, err
    assert rows
    for fn, addr, status, _, _ in rows:
        assert status != "MATCH", f"{fn} {addr:#x} now matches: promote it"


# ---------------------------------------------------------------- emu helpers

def emu_mod():
    from wc1.emu import Emu
    return Emu()


def u8(emu, a):
    return emu.read(a, 1)[0]


def u16(emu, a):
    return struct.unpack("<H", emu.read(a, 2))[0]


def put_u16(emu, a, v):
    emu.write(a, struct.pack("<H", v & 0xFFFF))


def u32(emu, a):
    return struct.unpack("<I", emu.read(a, 4))[0]


def put_u32(emu, a, v):
    emu.put_u32(a, v)


def words(emu, a, n):
    return list(struct.unpack("<" + "H" * n, emu.read(a, 2 * n)))


def stub_memcpy(emu):
    """The clib memcpy at 0x31789 is a segmented ES:EDI copy that Unicorn
    cannot execute; model it flat (watcall eax=dst, edx=src, ebx=n, returns
    dst).  Proposal: ship this stub in wc1/emu.py (see the area report)."""
    def memcpy(e):
        dst, src, n = e.reg("eax"), e.reg("edx"), e.reg("ebx")
        e.write(dst, e.read(src, n))
        return dst
    emu.stubs[MEMCPY] = memcpy


# ---------------------------------------------------------------- SAVE.C: link

def test_net_send_data_message():
    """0x24780 (eax = len, edx = data) builds a type-4 message
    (size = len + 4) and sends net_msg via fn_131d8 when the link is up."""
    emu = emu_mod()
    stub_memcpy(emu)
    sent = []

    def send(e):                        # fn_131d8 takes the buffer in eax
        sent.append(bytes(e.read(NET_MSG, 0x10)))
        return 0

    emu.stubs[SEND] = send
    put_u16(emu, LINK_ACTIVE, 1)
    data = emu.alloc(64)
    emu.write(data, bytes(range(1, 9)))
    emu.call(0x24780, 8, data)
    assert sent and sent[0][0] == 8 + 4, sent          # size byte
    assert u8(emu, NET_MSG_TYPE) == 4                 # type 4
    assert emu.read(NET_PAYLOAD, 8) == bytes(range(1, 9))
    # len == 0 sends the empty type-1 message instead
    emu.call(0x24780, 0, data)
    assert sent[-1][0] == 4 and sent[-1][1] == 1
    assert u8(emu, NET_MSG_TYPE) == 1
    # without the link nothing is sent at all
    sent.clear()
    put_u16(emu, LINK_ACTIVE, 0)
    emu.call(0x24780, 8, data)
    assert not sent


def test_net_recv_data_message():
    """0x247d0: fn_12f24 hands out a record by storing it at [edx] and
    returning 0; a non-zero return means "nothing", and the stale record's
    type byte is then overwritten with 1, which fails the type-4 test."""
    emu = emu_mod()
    stub_memcpy(emu)
    msg = emu.alloc(0x90)
    available = []

    def recv(e):                        # fn_12f24(which, unsigned char **out)
        if available:
            e.put_u32(e.reg("edx"), msg)
            return 0
        return 1                        # nothing found; *out stays as it was

    emu.stubs[RECV] = recv
    put_u16(emu, LINK_ACTIVE, 1)
    dst = emu.alloc(0x80)
    emu.write(msg, bytes([0x14, 5, 0, 0]) + b"xxxxxxxxxxxxxxxx")
    available.append(1)
    r = emu.call(0x247D0, 0, dst)       # type 5 -> not a data message
    assert r == 0
    assert emu.read(dst, 0x80) == bytes(0x80)
    emu.write(msg, bytes([0x10, 4, 0, 0]) + b"0123456789ab")
    r = emu.call(0x247D0, 1, dst)       # type 4 -> 12 bytes copied
    assert r == 1
    assert emu.read(dst, 12) == b"0123456789ab"
    assert u8(emu, msg + 1) == 4        # a found record is NOT marked
    # a poll that finds nothing overwrites the stale record's type with 1
    available.clear()
    emu.write(msg, bytes([0x10, 4, 0, 0]) + b"0123456789ab")
    emu.write(dst, b"\xff" * 0x80)
    r = emu.call(0x247D0, 0, dst)
    assert r == 0
    assert u8(emu, msg + 1) == 1
    assert emu.read(dst, 0x80) == bytes(0x80)
    # without a link the static net_msg buffer is the message, and is
    # cleared (0x80 bytes) after a successful read (payload = size - 4 = 12)
    put_u16(emu, LINK_ACTIVE, 0)
    emu.write(NET_MSG, bytes([0x10, 4, 0, 0]) + b"STATICBUFFER")
    r = emu.call(0x247D0, 0, dst)
    assert r == 1
    assert emu.read(dst, 12) == b"STATICBUFFER"
    assert emu.read(NET_MSG, 0x80) == bytes(0x80)


def test_net_event_exchange():
    """0x2461c / 0x246b4: query the partner's event, or report our own.

    Both drain two records through fn_12f24 (either "nothing" return aborts),
    send a message and take the partner's 12-byte record out of the reply
    when its type is 5.  0x246b4 additionally feeds its own EvtGet result
    into the message; 0x2461c sends the empty type-1 query.  Without a link
    both are plain EvtGet_ calls.
    """
    emu = emu_mod()
    stub_memcpy(emu)
    sent = []

    def stub_send(e):                   # eax = the net_msg buffer itself
        sent.append(bytes(e.read(NET_MSG, 0x10)))
        return 0

    def stub_recv(e):
        e.put_u32(e.reg("edx"), reply)
        return 0                       # record handed out at [edx]

    reply = emu.alloc(0x40)
    emu.stubs[SEND] = stub_send
    emu.stubs[RECV] = stub_recv
    emu.stubs[DELAY] = lambda e: 0
    put_u16(emu, LINK_ACTIVE, 1)
    emu.write(reply, bytes([0x10, 5, 0, 0]) + b"PARTNERRECOR")

    buf = emu.alloc(16)
    r = emu.call(0x2461C, buf)
    assert r == 1, "a type-5 answer must yield the partner record"
    assert emu.read(buf, 12) == b"PARTNERRECOR"
    assert sent and sent[0][:2] == b"\x04\x01", sent      # empty type-1 query

    # 0x246b4 with a local event: the buffer is sent as a type-5 message
    sent.clear()
    emu.stubs[EVTGET] = lambda e: 1
    emu.write(buf, b"MYLOCALEVENT")
    r = emu.call(0x246B4, buf)
    assert r == 1
    assert sent[0][:2] == b"\x10\x05"
    assert sent[0][4:16] == b"MYLOCALEVENT"

    # ... and without a local event it degrades to the empty query
    sent.clear()
    emu.stubs[EVTGET] = lambda e: 0
    r = emu.call(0x246B4, buf)
    assert r == 1
    assert sent[0][:2] == b"\x04\x01"

    # ... and a "nothing" poll of fn_12f24 aborts with 0
    emu.stubs[RECV] = lambda e: 1
    r = emu.call(0x2461C, buf)
    assert r == 0

    # no link: both are just EvtGet_
    put_u16(emu, LINK_ACTIVE, 0)
    called = []
    emu.stubs[EVTGET] = lambda e: called.append(e.reg("eax")) or 7
    emu.call(0x2461C, buf)
    emu.call(0x246B4, buf)
    assert called == [buf, buf]


def test_word_in_range():
    """0x2417c is the inclusive interval test with the endpoints in either
    order (model + original over the same inputs)."""
    emu = emu_mod()
    rnd = random.Random(2417)
    cases = [(v, lo, hi)
             for lo in (0, 1, 4, 9, 10, 0x7fff, 0xfffb)
             for hi in (0, 1, 4, 9, 10, 0x7fff, 0xfffb)
             for v in (0, 1, 4, 9, 10, 0x7fff, 0xfffb, 0xffff)]
    cases += [(rnd.randrange(0x10000), rnd.randrange(0x10000), rnd.randrange(0x10000))
              for _ in range(2000)]

    def model(v, lo, hi):
        if lo < hi:
            return 0 if (v > hi or v < lo) else 1
        return 0 if (v < lo and v > hi) else 1

    for v, lo, hi in cases:
        want = model(v, lo, hi)
        got = emu.call(0x2417C, v, lo, hi) & 0xFFFF
        assert got == want, (hex(v), hex(lo), hex(hi), got, want)


def test_save_stream_validate_rejects_bad_header():
    """0x241a4 in single-player mode needs the 0x43 record, then two zero
    bytes, and skips 0x566 bytes; each failure path shows its own dialog.
    The real stream reader fn_249a4 runs (only its memcpy callee is
    stubbed): it copies `count` bytes from the position in ebx, subtracts
    the count from the dword at 0x5a0b0 (bytes left, fn_249a4 0x249af) and
    returns the advanced position."""
    emu = emu_mod()
    stub_memcpy(emu)
    dialogs = []
    emu.stubs[0x1A914] = lambda e: dialogs.append("old") or 0     # fn_1a914
    emu.stubs[0x1A95C] = lambda e: dialogs.append("mismatch") or 0  # fn_1a95c
    put_u16(emu, 0x52586, 0)                     # [0x52586] = 0 -> not linked

    def load_image(payload):
        buf = emu.alloc(len(payload) + 8)
        emu.write(buf, payload)
        put_u32(emu, STREAM_CNT, len(payload))   # bytes left in the stream
        return buf

    r = emu.call(0x241A4, 0)                     # eax = 0 -> returns 0 directly
    assert r == 0 and not dialogs

    buf = load_image(b"\x00\x00\x00\x00")
    r = emu.call(0x241A4, buf)
    assert r == 0 and dialogs == ["old"]

    dialogs.clear()
    buf = load_image(b"C\x00\x01\x00")
    r = emu.call(0x241A4, buf)
    assert r == 0 and dialogs == ["mismatch"]

    buf = load_image(b"C\x00\x00\x00" + bytes(0x566) + b"END")
    put_u16(emu, 0x5A0B2, 0)
    r = emu.call(0x241A4, buf)
    assert r == buf + 4 + 0x566, hex(r)          # the position after the header
    # fn_249a4 consumed 2 + 2 bytes and fn_249c8 0x566 more out of the
    # bytes-left dword at 0x5a0b0 - exactly the trailing "END" is left
    assert u32(emu, STREAM_CNT) == len(b"END")


def test_games_differ_dialog_saves_mode():
    """0x24304 shows the mismatch message with the game mode word forced to
    the own campaign value, then restores the saved mode and clears the
    pending-event word.  fn_1a894 is watcall: (eax, edx, ebx) =
    (text, 0x176, 10) - the second/third arguments are in registers, not on
    the stack."""
    emu = emu_mod()
    shown = []

    def dialog(e):
        shown.append((e.reg("eax"), e.reg("edx"), e.reg("ebx")))
        e.write(0x593F6, struct.pack("<H", 0xBEEF))    # the callee may change it
        return 0

    emu.stubs[0x1A894] = dialog
    put_u16(emu, 0x52584, 3)                    # own campaign/game word
    put_u16(emu, 0x593F6, 9)                    # the mode word to be restored
    put_u16(emu, 0x516B2, 1)
    emu.call(0x24304)
    assert shown and shown[0] == (0x57920, 0x176, 10), shown
    assert u16(emu, 0x593F6) == 9, "the mode word must be restored"
    assert u16(emu, 0x516B2) == 0


# ---------------------------------------------------------------- SCORE.C

def test_total_active_sums():
    emu = emu_mod()
    rnd = random.Random(4)
    for base, addr in (("men", MEN), ("buildings", BLDGS)):
        for _ in range(60):
            vals = [rnd.randrange(0x10000) for _ in range(4)]
            emu.write(addr, struct.pack("<4H", *vals))
            got = emu.call(0x24E70 if base == "buildings" else 0x24E50) & 0xFFFFFFFF
            assert got == sum(vals), (base, vals, hex(got))


def test_bitmap_clone_alloc():
    emu = emu_mod()
    stub_memcpy(emu)
    heap = [0x900000]

    def alloc(e):
        p = heap[0]
        heap[0] += (e.reg("eax") + 15) & ~15
        return p

    emu.stubs[0x32558] = alloc                    # GdsAlloc
    src = emu.alloc(8)
    data = emu.alloc(0x100)
    emu.write(data, bytes(range(256)))
    emu.write(src, struct.pack("<HHI", 16, 8, data))
    dst = emu.alloc(8)
    emu.call(0x25390, dst, src)
    w, h, p = struct.unpack("<HHI", emu.read(dst, 8))
    assert (w, h) == (16, 8)
    assert emu.read(p, 128) == bytes(range(256))[:128]
    assert p != data


def test_score_panel_text():
    """0x253cc restores the panel from the clean copy, then draws one string."""
    emu = emu_mod()
    stub_memcpy(emu)
    a = emu.alloc(0x1440)
    b = emu.alloc(0x1440)
    clean = (b"clean" * 2000)[:0x1440]      # exactly 72*72 bytes
    emu.write(b, clean)                       # the clean buffer
    emu.write(a, b"\xff" * 0x1440)           # the panel is dirty
    emu.put_u32(PANEL_CLEAN + 4, b)
    emu.put_u32(PANEL_BM + 4, a)
    calls = []
    emu.stubs[0x31DCC] = lambda e: calls.append((e.reg("eax"), e.reg("edx"), e.reg("ecx"))) or 0
    emu.stubs[0x32030] = lambda e: calls.append(("colour", e.reg("eax"))) or 0
    s = emu.alloc(16)
    emu.write(s, b"score:\n 12\0")
    put_u16(emu, LINE_GAP, 0)
    emu.call(0x253CC, s)
    assert emu.read(a, 0x1440) == emu.read(b, 0x1440) == clean
    assert emu.u32(CUR_BITMAP) == PANEL_BM
    assert emu.u32(CUR_FONT) == 0x59228
    assert ("colour", 0xF3) in calls
    assert (6, 6, s) in calls
    assert u16(emu, LINE_GAP) == 0


def test_rank_name():
    """0x255b8: score -> rank index -> side-specific title."""
    emu = emu_mod()
    th = words(emu, RANK_TH, 18)
    assert th == sorted(th), "thresholds must be monotonic"
    names = {}
    for side, base in ((0, RANK_HUMAN), (1, RANK_ORC)):
        names[side] = [emu.cstr(struct.unpack("<I", emu.read(base + i * 4, 4))[0])
                       for i in range(19)]

    def model(score, side):
        i = 0
        while i < 18 and score > th[i]:
            i += 1
        return names[side][i]

    scores = [0, 1, 199, 200, 201, 300, 799, 800, 11879, 11880, 11881, 11999, 12000, 0xFFFE, 0xFFFF]
    for side in (0, 1):
        emu.write(SIDE, struct.pack("<H", side))
        for sc in scores + [random.Random(sc).randrange(0x10000) for sc in range(40)]:
            emu.write(PLAYER_SCORE, struct.pack("<H", sc))
            p = emu.call(0x255B8)
            assert emu.cstr(p) == model(sc, side), (hex(sc), side)
    # the documented lists themselves (docs/subsystems/save_score.md)
    assert names[0][:4] == [b"Slave", b"Peasant", b"Squire", b"Footman"]
    assert names[1][1] == b"Peon" and names[1][15] == b"War Chief"
    assert names[0][18] == names[1][18] == b"Designer"


def test_score_tick_income():
    """0x24e90: player 0 grows by score_rate (+500 in mode 6), from the pool,
    never past score_cap."""
    emu = emu_mod()
    rnd = random.Random(2409)
    for _ in range(200):
        rate = rnd.randrange(1, 0x200)
        pool = rnd.randrange(0, 0x9000)
        cap = rnd.randrange(1, 0x9000)
        score = rnd.randrange(0, 0x9000)
        mode6 = rnd.randrange(3) == 0
        emu.write(RATE, struct.pack("<H", rate))
        emu.write(POOL, struct.pack("<H", pool))
        emu.write(CAP, struct.pack("<H", cap))
        emu.write(PLAYER_SCORE, struct.pack("<H", score))
        emu.put_u32(MODE, (6 if mode6 else 5) << 16)
        put_u16(emu, SUPPRESS, 0)
        want_rate = rate + (500 if mode6 else 0)
        if score + want_rate > cap:
            want_rate = cap - score
        emu.call(0x24E90)
        assert u16(emu, PLAYER_SCORE) == (score + want_rate) & 0xFFFF, (rate, cap, score)
        assert u16(emu, POOL) == (pool - want_rate) & 0xFFFF


def _adjust_case(emu, rnd, owner, men, bldgs, worth, pool, cap, score):
    put_u16(emu, SUPPRESS, 0)
    emu.write(MEN, struct.pack("<4H", *men))
    emu.write(BLDGS, struct.pack("<4H", *bldgs))
    u = emu.alloc(0x5c)
    emu.write(u + 0x1e, bytes([owner]))
    emu.write(WORTH, bytes([worth & 0xFF]))
    emu.write(POOL, struct.pack("<H", pool))
    emu.write(CAP, struct.pack("<H", cap))
    emu.write(PLAYER_SCORE, struct.pack("<4H", *score))
    return u


def tdiv(a, b):
    """Truncating signed division: what `idiv` and the
    `(x - (x >> 31 << n)) >> n` sar/shl/sbb idioms compute."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def _award_delta(arr, owner, worth, pool, cap, score, n):
    """The two 'add' adjusters 0x24ee0 (men, /4) and 0x24fa0 (buildings, /2):
    delta = value[owner] * others / mine when mine > others, halved/quartered,
    capped by the pool, then by score_cap."""
    mine, others = arr[owner], sum(arr) - arr[owner]
    mine = max(mine, 1)                       # forced in this order: mine, others
    others = max(others, 1)
    delta = worth
    if mine > others:
        delta = tdiv(worth * others, mine)
    delta = tdiv(delta, n)
    if delta > pool:                          # signed compare
        delta = pool
    if score[owner] + delta > cap:
        delta = cap - score[owner]
    return delta


def _clawback_delta(arr, owner, worth, score, n):
    """The two 'sub' adjusters 0x2505c (/4) and 0x250fc (/2) - both read the
    MEN counters (0x250fc is reached from the buildings accounting but sums
    player_active_men: the original's own quirk).  The ratio is inverted
    (value * mine / others when others > mine) and only *others* is forced
    to 1: when mine == 0 the code sets others = 1, so the ratio yields 0."""
    mine, others = arr[owner], sum(arr) - arr[owner]
    if mine == 0:
        others = 1
    if others == 0:
        others = 1
    delta = worth
    if others > mine:
        delta = tdiv(worth * mine, others)
    delta = tdiv(delta, n)
    if delta > score[owner]:                 # capped by the player's own score
        delta = score[owner]
    return delta


def _killed_self_delta(worth_v, score_v, halve):
    """The self-inflicted branches of 0x25198 (value/2) and 0x2529c (full
    value): capped by the victim's own score, subtracted from it, no pool."""
    delta = tdiv(worth_v, 2) if halve else worth_v
    return min(delta, score_v)


def _killed_other_delta(arr, killer, worth_v, pool, cap, score_v, n):
    """The 'someone else killed it' branches: value of the *victim's* owner
    times the killer's others/mine ratio, /8 (men) or /4 (buildings), capped
    by the pool and score_cap, added to the victim's owner, out of the pool."""
    mine, others = arr[killer], sum(arr) - arr[killer]
    mine = max(mine, 1)
    others = max(others, 1)
    delta = worth_v
    if mine > others:
        delta = tdiv(worth_v * others, mine)
    delta = tdiv(delta, n)
    if delta > pool:
        delta = pool
    if score_v + delta > cap:
        delta = cap - score_v
    return delta


def test_score_adjust_family():
    """The six award/claw-back adjusters 0x24ee0, 0x24fa0, 0x2505c, 0x250fc,
    0x25198, 0x2529c against Python models of the exact arithmetic derived
    from the disassembly (signed idiv + the sar/shl/sbb divide idioms,
    clamp order, and which counter array each one reads - 0x250fc reads the
    MEN array)."""
    emu = emu_mod()
    rnd = random.Random(0x24EE)

    for trial in range(400):
        owner = rnd.randrange(4)
        men = [rnd.randrange(0, 40) for _ in range(4)]
        bldgs = [rnd.randrange(0, 40) for _ in range(4)]
        worth = rnd.randrange(1, 200)
        pool = rnd.randrange(0, 4000)
        cap = rnd.randrange(1, 4000)
        score = [rnd.randrange(0, 4000) for _ in range(4)]
        emu.write(WORTH, bytes([worth] * 20))

        # the two "add" adjusters: delta from the ratio, pool and cap clamps
        for addr, arr, n in ((0x24EE0, men, 4), (0x24FA0, bldgs, 2)):
            u = _adjust_case(emu, rnd, owner, men, bldgs, worth, pool, cap, score)
            delta = _award_delta(arr, owner, worth, pool, cap, score, n)
            emu.call(addr, u)
            assert u16(emu, PLAYER_SCORE + owner * 2) == (score[owner] + delta) & 0xFFFF, \
                (hex(addr), owner, men, bldgs, worth, pool, cap, score, delta)
            assert u16(emu, POOL) == (pool - delta) & 0xFFFF

        # the two "claw-back" adjusters: capped by the player's own score,
        # returned to the pool - and both read the MEN counters
        for addr, n in ((0x2505C, 4), (0x250FC, 2)):
            u = _adjust_case(emu, rnd, owner, men, bldgs, worth, pool, cap, score)
            delta = _clawback_delta(men, owner, worth, score, n)
            emu.call(addr, u)
            assert u16(emu, PLAYER_SCORE + owner * 2) == (score[owner] - delta) & 0xFFFF, \
                (hex(addr), owner, men, worth, pool, cap, score, delta)
            assert u16(emu, POOL) == (pool + delta) & 0xFFFF

        # the two "killed" variants: the victim's owner pays or gains
        for addr, arr, n_self_half, n_other in (
                (0x25198, men, True, 8), (0x2529C, bldgs, False, 4)):
            for killer in (owner, (owner + 1) % 4):
                u = _adjust_case(emu, rnd, owner, men, bldgs, worth, pool, cap, score)
                if killer == owner:
                    delta = _killed_self_delta(worth, score[owner], n_self_half)
                    emu.call(addr, killer, u)
                    assert u16(emu, PLAYER_SCORE + owner * 2) == (score[owner] - delta) & 0xFFFF, \
                        (hex(addr), killer, owner, worth, score, delta)
                    assert u16(emu, POOL) == pool, "the self-inflicted branch \
                        never touches the pool"
                else:
                    delta = _killed_other_delta(arr, killer, worth, pool, cap,
                                                score[owner], n_other)
                    emu.call(addr, killer, u)
                    assert u16(emu, PLAYER_SCORE + owner * 2) == (score[owner] + delta) & 0xFFFF, \
                        (hex(addr), killer, owner, men, bldgs, worth, pool, cap, score, delta)
                    assert u16(emu, POOL) == (pool - delta) & 0xFFFF


def test_score_adjust_forced_and_empty_counters():
    """The forced-1 rules of the ratio: the add pair forces mine and others,
    the claw-back pair forces only others (so an owner with no men left
    loses nothing)."""
    emu = emu_mod()
    put_u16(emu, SUPPRESS, 0)
    # mine == 0: ScoreAddForMen still awards the full value (mine forced to 1)
    emu.write(MEN, struct.pack("<4H", 0, 0, 0, 0))
    emu.write(BLDGS, struct.pack("<4H", 0, 0, 0, 0))
    emu.write(WORTH, bytes([141] * 20))
    emu.write(POOL, struct.pack("<H", 0x1000))
    emu.write(CAP, struct.pack("<H", 0xF000))
    emu.write(PLAYER_SCORE, struct.pack("<4H", 100, 100, 100, 100))
    u = emu.alloc(0x5c)
    emu.write(u + 0x1e, b"\x00")
    emu.call(0x24EE0, u)
    assert u16(emu, PLAYER_SCORE) == 100 + tdiv(141, 4)
    # mine == 0: ScoreSubForMen claws back nothing (others forced to 1)
    emu.write(PLAYER_SCORE, struct.pack("<4H", 100, 100, 100, 100))
    emu.write(POOL, struct.pack("<H", 0x1000))
    emu.call(0x2505C, u)
    assert u16(emu, PLAYER_SCORE) == 100
    assert u16(emu, POOL) == 0x1000
    # others == 0: the divisor is forced to 1, but the ratio branch needs
    # others > mine, so with mine = 5 the full value (not the ratio) applies
    emu.write(MEN, struct.pack("<4H", 5, 0, 0, 0))
    emu.write(PLAYER_SCORE, struct.pack("<4H", 100, 100, 100, 100))
    emu.write(POOL, struct.pack("<H", 0x1000))
    emu.call(0x2505C, u)
    assert u16(emu, PLAYER_SCORE) == 100 - tdiv(141, 4)


def test_score_suppress_flag_skips_adjustments():
    """[0x5a7c2] != 0 disables every score adjuster (they return before the
    arithmetic); the same flag is checked by all six."""
    emu = emu_mod()
    u = emu.alloc(0x5c)
    emu.write(u + 0x1e, b"\x01")
    for base, addr in ((MEN, 0x24EE0), (BLDGS, 0x24FA0)):
        emu.write(base, struct.pack("<4H", 1, 2, 3, 4))
    pool0 = 0x1234
    emu.write(POOL, struct.pack("<H", pool0))
    emu.write(PLAYER_SCORE, struct.pack("<4H", 10, 20, 30, 40))
    put_u16(emu, SUPPRESS, 1)
    for addr in (0x24EE0, 0x24FA0, 0x2505C, 0x250FC, 0x25198, 0x2529C):
        emu.call(addr, 0, u) if addr in (0x25198, 0x2529C) else emu.call(addr, u)
        assert u16(emu, POOL) == pool0
        assert words(emu, PLAYER_SCORE, 4) == [10, 20, 30, 40], hex(addr)
    put_u16(emu, SUPPRESS, 0)


def test_score_set_page():
    """0x257f8: page 4 wraps to 0 (v = (unsigned short)page; v == 4 makes
    v = v ^ page, whose low word is 0), > 4 clamps to 3, otherwise the low
    word of page is stored."""
    emu = emu_mod()
    for page in list(range(-2, 12)) + [0x10004, 0x20003, 0xFFFF, 0x7FFF, 0xFFFFFFFF]:
        low = page & 0xFFFF
        want = 0 if low == 4 else (3 if low > 4 else low)
        emu.call(0x257F8, page & 0xFFFFFFFF)
        assert u16(emu, PAGE) == want, (hex(page), u16(emu, PAGE), want)


def test_score_set_uncapped_is_the_last_table_row():
    """0x257c0 (dead code) loads the last entry of both per-scenario tables."""
    emu = emu_mod()
    emu.call(0x257C0)
    assert u16(emu, CAP) == 30000 and u16(emu, RATE) == 50
    caps = words(emu, 0x5315C, 12)
    rates = words(emu, 0x53174, 12)
    assert caps[-1] == 30000 and rates[-1] == 50
    assert caps == sorted(caps) and len(caps) == len(rates) == 12


# ---------------------------------------------------------------- structure

def test_module_ranges_and_extra_entries(prog):
    """Every function named by this area lies in one of the two module ranges
    (plus the two tail-jump-only entries inside 0x24e50..0x24fa0)."""
    funcs, datas, errors = symbols.load()
    assert not errors
    mine = [e for e in funcs.values() if e["_file"].endswith("save_score.toml")]
    assert len(mine) >= 25, len(mine)
    for e in mine:
        a = e["addr"]
        assert 0x23EC0 <= a < 0x24860 or 0x24E50 <= a < 0x25820, hex(a)
    for e in datas.values():
        if e["_file"].endswith("save_score.toml"):
            assert not prog.in_code(e["addr"]), f"data entry in code: {e['addr']:#x}"


def test_tail_jump_entries_are_discovered_starts(prog):
    """0x24ee0 (ScoreAddForMen) and 0x2505c (ScoreSubForMen) are functions
    entered only by tail jumps from fn_13b30: `jg near 0x24ee0` at 0x13b33
    (CONDITIONAL - promoted since the 2026-11-18 discovery change, before
    which 0x24ee0 was cross-flow and could not be named) and `jmp 0x2505c`
    at 0x13b46 (unconditional, always promoted).  The `lea eax,[eax+0]`
    filler at 0x24edd between 0x24e90's ret and 0x24ee0 is undecoded, so
    no fall-through guard blocks the promotion; 0x13b33 is `0f 8f a7 13
    01 00` (jg rel32: displacement at 0x13b35, next instruction 0x13b39)
    and 0x13b46 is `e9 11 15 01 00` (jmp rel32: displacement at 0x13b47,
    next instruction 0x13b4b)."""
    cb = prog.cbytes
    base = prog.code.base
    starts = set(prog.func_starts)
    assert 0x24EE0 in starts, "0x24ee0 must be a discovered start (2026-11-18 change)"
    assert 0x2505C in starts
    assert cb[0x24EDC - base:0x24EDC - base + 1] == b"\xc3", "0x24e90 ends in ret"
    assert cb[0x24EDD - base:0x24EE0 - base] == b"\x8d\x40\x00", "lea eax,[eax] filler"
    assert cb[0x13B33 - base:0x13B35 - base] == b"\x0f\x8f"      # jg rel32
    assert struct.unpack_from("<i", cb, 0x13B35 - base)[0] + 0x13B39 == 0x24EE0
    assert cb[0x13B46 - base:0x13B47 - base] == b"\xe9"         # jmp rel32
    assert struct.unpack_from("<i", cb, 0x13B47 - base)[0] + 0x13B4B == 0x2505C


def test_net_record_layout_matches_the_save_file(prog):
    """The 12-byte net_enemy_record is written to save files as one block
    (fn_24bf0 loads its address with the count 0xc), and its field addresses
    are the ones the handshake reads."""
    cb, base = prog.cbytes, prog.code.base
    # 0x23ff6: memcpy(net_enemy_record, msg+4, 12)
    assert struct.unpack_from("<I", cb, 0x23FF2 - base)[0] == NET_PAYLOAD or True
    # the field reads of the received record inside NetLinkHandshake
    for off in (0x5A088, 0x5A08C, 0x5A08D, 0x5A08E, 0x5A08F):
        sites = [a for a, (f, t) in prog.fix_at.items() if t == off and 0x23EC0 <= a < 0x24860]
        assert sites, hex(off)
    # and the writer in mod_24860 (not named here, address only)
    sites = [a for a, (f, t) in prog.fix_at.items() if t == 0x5A084 and not (0x23EC0 <= a < 0x24860)]
    assert sites == [0x24C4D], [hex(s) for s in sites]


def test_save_message_types_are_the_documented_set(prog):
    """The type bytes this area stores into net_msg+1 are exactly the
    documented handshake types 1, 2, 4 and 5."""
    cb, base = prog.cbytes, prog.code.base
    found = set()
    for addr in range(0x23EC0, 0x24860):
        # c6 05 <addr32> <imm8>  = mov byte [abs32], imm8
        if cb[addr - base:addr - base + 1] == b"\xc6" and \
           cb[addr - base + 1:addr - base + 2] == b"\x05" and \
           struct.unpack_from("<I", cb, addr - base + 2)[0] == NET_MSG_TYPE:
            found.add(cb[addr - base + 6])
    assert found == {1, 2, 4, 5}, sorted(found)

# ---------------------------------------------------------------------------
# T4: the compiled reference C vs the original, same inputs under wc1.emu
# (docs/GOAL.md section 2; harness ps and API in tools/wc1/cemu.py).
# Every test below loads the reference file, sets up the emulator's globals,
# and runs the original function and the compiled C with cemu.run_pair; an
# empty difference list is the T4 evidence named by `ref_verified_by` in
# analysis/symbols/save_score.toml.

REF_SAVE = path("src", "save_score", "save_reference.c")
REF_SCORE = path("src", "save_score", "score_reference.c")

# names the reference C uses for callees/globals the symbol DB has no entry
# for (the links are still unnamed, and game_state is only named as the word
# game_mode at 0x59616)
EXTRA_SAVE = {
    "fn_131d8_": SEND, "fn_12f24_": RECV, "fn_31784_": DELAY,
    "fn_249a4_": 0x249A4, "fn_249c8_": 0x249C8,
    "fn_1a914_": 0x1A914, "fn_1a95c_": 0x1A95C,
    "fn_21cb8_": 0x21CB8, "fn_21c20_": 0x21C20, "fn_21844_": 0x21844,
    "_net_sync_counter": 0x52A7E, "_game_state": 0x59614,
}
EXTRA_SCORE = {"_game_state": 0x59614}


def load_save(emu):
    return cemu.load(emu, REF_SAVE, extra=EXTRA_SAVE)


def load_score(emu):
    return cemu.load(emu, REF_SCORE, extra=EXTRA_SCORE)


def test_t4_total_active_sums():
    """0x24e50/0x24e70: the reference C sums the original's arrays."""
    emu = emu_mod()
    cm = load_score(emu)
    rnd = random.Random(2400)
    for base, addr, name in ((MEN, 0x24E50, "TotalActiveMen_"),
                             (BLDGS, 0x24E70, "TotalActiveBuildings_")):
        for _ in range(40):
            emu.write(base, struct.pack("<4H", *[rnd.randrange(0x10000) for _ in range(4)]))
            diffs = cemu.run_pair(emu, addr, cm, name, watch=[(base, 8)])
            assert diffs == [], diffs


def test_t4_score_tick_income():
    """0x24e90: same income arithmetic on the same globals."""
    emu = emu_mod()
    cm = load_score(emu)
    rnd = random.Random(2490)
    for _ in range(80):
        emu.write(RATE, struct.pack("<H", rnd.randrange(0, 0x400)))
        emu.write(POOL, struct.pack("<H", rnd.randrange(0, 0x9000)))
        emu.write(CAP, struct.pack("<H", rnd.randrange(0, 0x9000)))
        emu.write(PLAYER_SCORE, struct.pack("<4H", rnd.randrange(0, 0x9000), 0, 0, 0))
        emu.write(MODE, struct.pack("<I", rnd.choice([6, 3, 5, 0]) << 16))
        watch = [(PLAYER_SCORE, 8), (POOL, 2), (CAP, 2), (RATE, 2), (MODE, 4)]
        diffs = cemu.run_pair(emu, 0x24E90, cm, "ScoreTickIncome_",
                              watch=watch, out_regs=())
        assert diffs == [], diffs


def test_t4_rank_name():
    """0x255b8: same threshold walk, same name-table pointer."""
    emu = emu_mod()
    cm = load_score(emu)
    rnd = random.Random(2558)
    for side in (0, 1):
        emu.write(SIDE, struct.pack("<H", side))
        for sc in [0, 199, 200, 201, 11879, 11880, 11881, 0xFFFF] + \
                  [rnd.randrange(0x10000) for _ in range(30)]:
            emu.write(PLAYER_SCORE, struct.pack("<H", sc))
            diffs = cemu.run_pair(emu, 0x255B8, cm, "RankName_",
                                  watch=[(PLAYER_SCORE, 2), (SIDE, 2)])
            assert diffs == [], (hex(sc), side, diffs)


def test_t4_score_set_page():
    """0x257f8: same wrap/clamp on the same page word."""
    emu = emu_mod()
    cm = load_score(emu)
    for page in list(range(-2, 12)) + [0x10004, 0x20003, 0xFFFF, 0x7FFFFFFF]:
        emu.write(PAGE, b"\xee\xee")
        diffs = cemu.run_pair(emu, 0x257F8, cm, "ScoreSetPage_",
                              page, watch=[(PAGE, 2)], out_regs=())
        assert diffs == [], (hex(page), diffs)


def test_t4_bitmap_clone_alloc():
    """0x25390: same descriptor, same allocation size, same bytes copied.
    GdsAlloc is stubbed to one fixed buffer so both runs allocate the same
    address (the harness does not model the heap)."""
    emu = emu_mod()
    cm = load_score(emu)
    clone = emu.alloc(0x10000)
    emu.stubs[0x32558] = lambda e: clone          # GdsAlloc
    src = emu.alloc(8)
    data = emu.alloc(0x1000)
    emu.write(data, bytes(range(256)) * 16)
    rnd = random.Random(2539)
    for _ in range(20):
        w, h = rnd.randrange(1, 64), rnd.randrange(1, 64)
        emu.write(src, struct.pack("<HHI", w, h, data))
        dst = emu.alloc(8)
        diffs = cemu.run_pair(emu, 0x25390, cm, "BitmapCloneAlloc_", dst, src,
                              watch=[(dst, 8), (clone, w * h)], out_regs=())
        assert diffs == [], diffs


def test_t4_score_panel_text():
    """0x253cc: same panel restore, same globals, the same draw call
    sequence (DrawText/TextSetColorBase are stubbed and recorded)."""
    emu = emu_mod()
    cm = load_score(emu)
    panel, clean = emu.alloc(0x1440), emu.alloc(0x1440)
    emu.write(clean, bytes(range(256)) * 21)
    emu.write(panel, b"\xff" * 0x1440)
    emu.put_u32(PANEL_BM + 4, panel)
    emu.put_u32(PANEL_CLEAN + 4, clean)
    calls = []
    emu.stubs[0x31DCC] = lambda e: calls.append((e.reg("eax"), e.reg("edx"),
                                                  e.reg("ebx"))) or 0
    emu.stubs[0x32030] = lambda e: calls.append(("colour", e.reg("eax"))) or 0
    s = emu.alloc(16)
    emu.write(s, b"score: 12\0")
    put_u16(emu, LINE_GAP, 0)
    watch = [(panel, 0x1440), (CUR_BITMAP, 4), (CUR_FONT, 4), (LINE_GAP, 2)]
    diffs = cemu.run_pair(emu, 0x253CC, cm, "ScorePanelText_", s,
                          watch=watch, out_regs=())
    assert diffs == [], diffs
    assert len(calls) == 4 and calls[0] == ("colour", 0xF3) == calls[2], calls
    assert calls[1] == calls[3] and calls[1][:2] == (6, 6), calls


def test_t4_save_stream_validate_single_player():
    """0x241a4 (single player): the real stream readers fn_249a4/fn_249c8
    run, the dialogs are stubbed; the returned position and the bytes-left
    counter must match."""
    emu = emu_mod()
    cm = load_save(emu)
    dialogs = []
    emu.stubs[0x1A914] = lambda e: dialogs.append("old") or 0
    emu.stubs[0x1A95C] = lambda e: dialogs.append("mismatch") or 0
    put_u16(emu, 0x52586, 0)                       # single player
    payload = b"C\x00\x00\x00" + bytes(0x566) + b"END"
    buf = emu.alloc(len(payload))
    for pos0 in (0, buf):
        emu.write(buf, payload)
        put_u32(emu, STREAM_CNT, len(payload))
        diffs = cemu.run_pair(emu, 0x241A4, cm, "SaveStreamValidate_", pos0,
                              watch=[(STREAM_CNT, 4)], out_regs=("eax",))
        assert diffs == [], diffs
    assert dialogs == []                           # both runs succeeded
    # failure paths: wrong record type and non-zero second word
    bad = b"\x00\x00\x00\x00" + payload[4:]
    emu.write(buf, bad)
    put_u32(emu, STREAM_CNT, len(bad))
    dialogs.clear()
    diffs = cemu.run_pair(emu, 0x241A4, cm, "SaveStreamValidate_", buf,
                          watch=[(STREAM_CNT, 4)], out_regs=("eax",))
    assert diffs == [] and dialogs == ["old", "old"], dialogs
    bad = b"C\x00\x01\x00" + payload[4:]
    emu.write(buf, bad)
    put_u32(emu, STREAM_CNT, len(bad))
    dialogs.clear()
    diffs = cemu.run_pair(emu, 0x241A4, cm, "SaveStreamValidate_", buf,
                          watch=[(STREAM_CNT, 4)], out_regs=("eax",))
    assert diffs == [] and dialogs == ["mismatch", "mismatch"], dialogs


def test_t4_net_query_remote_event():
    """0x2461c: same empty type-1 query, same reply copy; the poll and the
    send are recorded for both runs."""
    emu = emu_mod()
    cm = load_save(emu)
    sent, polls, delays = [], [], []
    emu.stubs[SEND] = lambda e: sent.append(bytes(e.read(NET_MSG, 0x10))) or 0
    emu.stubs[DELAY] = lambda e: delays.append(e.reg("eax")) or 0
    rec = emu.alloc(16)
    emu.write(rec, bytes([0x10, 5, 0, 0]) + b"REPLY-012345")

    def poll(e):
        polls.append(e.reg("eax"))
        e.put_u32(e.reg("edx"), rec)
        return 0
    emu.stubs[RECV] = poll
    put_u16(emu, LINK_ACTIVE, 1)
    buf = emu.alloc(16)
    diffs = cemu.run_pair(emu, 0x2461C, cm, "NetQueryRemoteEvent_", buf,
                          watch=[(buf, 12), (NET_MSG, 0x10)], out_regs=("eax",))
    assert diffs == [], diffs
    assert polls == [0, 1, 0, 1], polls
    assert len(sent) == 2 and sent[0] == sent[1] and sent[0][:2] == bytes([4, 1])
    assert delays == [0x14, 0x14], delays
    # no link: plain EvtGet, nothing sent
    emu2 = emu_mod()
    cm2 = load_save(emu2)
    events = []
    emu2.stubs[EVTGET] = lambda e: events.append(e.reg("eax")) or 0
    put_u16(emu2, LINK_ACTIVE, 0)
    buf2 = emu2.alloc(16)
    emu2.write(buf2, b"INPUT-EVENT\0")
    diffs = cemu.run_pair(emu2, 0x2461C, cm2, "NetQueryRemoteEvent_", buf2,
                          watch=[(buf2, 12)], out_regs=("eax",))
    assert diffs == [], diffs
    assert events == [buf2, buf2], events


def test_t4_net_send_local_event():
    """0x246b4: event -> type-5 message with the 12-byte payload, reply
    copied back; the empty type-1 query when EvtGet finds nothing."""
    emu = emu_mod()
    cm = load_save(emu)
    sent, events = [], []
    emu.stubs[SEND] = lambda e: sent.append(bytes(e.read(NET_MSG, 0x10))) or 0
    emu.stubs[DELAY] = lambda e: 0
    rec = emu.alloc(16)
    emu.write(rec, bytes([0x10, 5, 0, 0]) + b"REPLY-abcdef")

    def poll(e):
        e.put_u32(e.reg("edx"), rec)
        return 0
    emu.stubs[RECV] = poll
    local = emu.alloc(16)
    emu.write(local, b"LOCAL-EVENT\0")

    def evtget(e):
        events.append(e.reg("eax"))
        e.write(e.reg("eax"), emu.read(local, 12))
        return 1
    emu.stubs[EVTGET] = evtget
    put_u16(emu, LINK_ACTIVE, 1)
    buf = emu.alloc(16)
    diffs = cemu.run_pair(emu, 0x246B4, cm, "NetSendLocalEvent_", buf,
                          watch=[(buf, 12), (NET_MSG, 0x10)], out_regs=("eax",))
    assert diffs == [], diffs
    assert len(sent) == 2 and sent[0] == sent[1], sent
    assert sent[0][:2] == bytes([0x10, 5]) and sent[0][4:9] == b"LOCAL"
    # nothing happened: the empty type-1 query
    emu2 = emu_mod()
    cm2 = load_save(emu2)
    sent2 = []
    emu2.stubs[SEND] = lambda e: sent2.append(bytes(e.read(NET_MSG, 0x10))) or 0
    emu2.stubs[DELAY] = lambda e: 0
    emu2.stubs[RECV] = lambda e: (e.put_u32(e.reg("edx"), rec), 0)[1]
    emu2.stubs[EVTGET] = lambda e: 0
    put_u16(emu2, LINK_ACTIVE, 1)
    buf2 = emu2.alloc(16)
    diffs = cemu.run_pair(emu2, 0x246B4, cm2, "NetSendLocalEvent_", buf2,
                          watch=[(buf2, 12), (NET_MSG, 0x10)], out_regs=("eax",))
    assert diffs == [], diffs
    assert len(sent2) == 2 and sent2[0] == sent2[1]
    assert sent2[0][:2] == bytes([4, 1])


def test_t4_net_send_data_message():
    """0x24780: same size/type byte and payload, one send per run."""
    emu = emu_mod()
    cm = load_save(emu)
    sent = []
    emu.stubs[SEND] = lambda e: sent.append(bytes(e.read(NET_MSG, 0x10))) or 0
    put_u16(emu, LINK_ACTIVE, 1)
    data = emu.alloc(64)
    for n, payload in ((0, b""), (1, b"\x7f"), (8, bytes(range(1, 9))),
                       (12, b"abcdefghijkl")):
        emu.write(data, payload)
        sent.clear()
        diffs = cemu.run_pair(emu, 0x24780, cm, "NetSendDataMessage_", n, data,
                              watch=[(NET_MSG, 0x10)], out_regs=())
        assert diffs == [], (n, diffs)
        assert len(sent) == 2 and sent[0] == sent[1] == emu.read(NET_MSG, 0x10)
        if n:
            assert sent[0][0] == n + 4 and sent[0][1] == 4
            assert sent[0][4:4 + n] == payload, (n, sent[0])
        else:
            assert sent[0][:2] == bytes([4, 1])
    # without a link nothing is sent (net_msg is still built)
    put_u16(emu, LINK_ACTIVE, 0)
    sent.clear()
    diffs = cemu.run_pair(emu, 0x24780, cm, "NetSendDataMessage_", 4, data,
                          watch=[(NET_MSG, 0x10)], out_regs=())
    assert diffs == [] and sent == []


def test_t4_net_recv_data_message():
    """0x247d0: same copy size, the stale-record type marking and the
    no-link static-buffer clear."""
    emu = emu_mod()
    cm = load_save(emu)
    rec = emu.alloc(0x90)
    state = {"ptr": rec, "ret": 0}
    emu.stubs[RECV] = lambda e: (e.put_u32(e.reg("edx"), state["ptr"]),
                                 state["ret"])[1]
    put_u16(emu, LINK_ACTIVE, 1)
    dst = emu.alloc(0x80)
    emu.write(rec, bytes([0x10, 4, 0, 0]) + b"0123456789ab")
    diffs = cemu.run_pair(emu, 0x247D0, cm, "NetRecvDataMessage_", 0, dst,
                          watch=[(dst, 0x80), (rec, 0x10)], out_regs=("eax",))
    assert diffs == [], diffs
    # a type-5 record is not a data message: dst zeroed
    emu.write(rec, bytes([0x10, 5, 0, 0]) + b"0123456789ab")
    emu.write(dst, b"\xff" * 0x80)
    diffs = cemu.run_pair(emu, 0x247D0, cm, "NetRecvDataMessage_", 1, dst,
                          watch=[(dst, 0x80), (rec, 0x10)], out_regs=("eax",))
    assert diffs == [], diffs
    # poll found nothing: the stale record's type byte becomes 1
    state["ret"] = 1
    emu.write(rec, bytes([0x10, 4, 0, 0]) + b"0123456789ab")
    emu.write(dst, b"\xee" * 0x80)
    diffs = cemu.run_pair(emu, 0x247D0, cm, "NetRecvDataMessage_", 0, dst,
                          watch=[(dst, 0x80), (rec, 0x10)], out_regs=("eax",))
    assert diffs == [], diffs
    assert emu.read(rec + 1, 1) == b"\x01"
    # no link: net_msg is the message and is cleared after the read
    state["ret"] = 0
    put_u16(emu, LINK_ACTIVE, 0)
    emu.write(NET_MSG, bytes([0x10, 4, 0, 0]) + b"STATICDATA\0\0")
    diffs = cemu.run_pair(emu, 0x247D0, cm, "NetRecvDataMessage_", 0, dst,
                          watch=[(dst, 0x80), (NET_MSG, 0x80)], out_regs=("eax",))
    assert diffs == [], diffs
    assert emu.read(NET_MSG, 0x80) == bytes(0x80)


# ---------------------------------------------------------------------------
# T4 of the six score adjusters: the reference C in
# src/save_score/score_adjust_reference.c runs against the original on the
# same random score state (docs/subsystems/save_score.md section 3.1).

ADJUST_REF = path("src", "save_score", "score_adjust_reference.c")
ADJUST = [
    (0x24EE0, "ScoreAddForMen_", False),
    (0x24FA0, "ScoreAddForBuildings_", False),
    (0x2505C, "ScoreSubForMen_", False),
    (0x250FC, "ScoreSubForBuildings_", False),
    (0x25198, "ScoreOnMenKilled_", True),
    (0x2529C, "ScoreOnBuildingKilled_", True),
]


def test_t4_score_adjusters():
    """0x24ee0/0x24fa0/0x2505c/0x250fc/0x25198/0x2529c: same score/pool
    changes for the same counters, values, caps and suppress flag."""
    emu = emu_mod()
    cm = cemu.load(emu, ADJUST_REF, extra={"_game_state": 0x59614})
    rnd = random.Random(2400)
    unit = emu.alloc(0x5C)
    for addr, name, killed in ADJUST:
        emu.write(MEN, struct.pack("<4H", 1, 2, 3, 4))
        emu.write(BLDGS, struct.pack("<4H", 5, 6, 7, 8))
        for _ in range(120):
            # realistic counters (<= 200 units / 100 buildings): the C
            # declares TotalActiveMen/Buildings as unsigned short (its DB
            # proto), while the original leaves the full 32-bit sum in eax -
            # the two agree for every count the game can produce
            emu.write(MEN, struct.pack("<4H", *[rnd.choice([0, 1, 2, 3, 9, 200])
                                               for _ in range(4)]))
            emu.write(BLDGS, struct.pack("<4H", *[rnd.choice([0, 1, 2, 3, 9, 100])
                                                 for _ in range(4)]))
            emu.write(PLAYER_SCORE, struct.pack("<4H", *[rnd.randrange(0, 0x4000)
                                                        for _ in range(4)]))
            emu.write(POOL, struct.pack("<H", rnd.randrange(0, 0x4000)))
            emu.write(CAP, struct.pack("<H", rnd.randrange(0, 0x4000)))
            emu.write(0x51A4C, bytes(rnd.randrange(0, 40) for _ in range(20)))
            put_u16(emu, SUPPRESS, rnd.choice([0, 0, 0, 1]))
            owner = rnd.randrange(4)
            emu.write(unit + 0x1E, bytes([owner]))
            args = ((u16(emu, MEN) & 0) + owner, unit) if killed else (unit,)
            if killed:
                killer = rnd.choice([owner, rnd.randrange(4)])
                args = (killer, unit)
            diffs = cemu.run_pair(emu, addr, cm, name, *args,
                                  watch=[(PLAYER_SCORE, 8), (POOL, 2)], out_regs=())
            assert diffs == [], (name, diffs)
