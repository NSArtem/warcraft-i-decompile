"""T4 differential tests for NETWORK.C (0x1f050..0x1fb0b)."""
import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.emu import Emu

pytestmark = pytest.mark.skipif(
    not os.path.isdir(path("analysis", "symbols")),
    reason="symbol DB / original image not available")

T4Stub = t4spec.T4Stub
T4Case = t4spec.T4Case
D = "src/network/"

IPX_BUF, ERR_TEXT = 0x59a00, 0x59ba8
SIG, NODE_NUM = 0x52984, 0x52a7c
KEY1, KEY46 = 0x5a8d6, 0x5a930
OWN_CAMP, MODEM_LINK, NET_RESP = 0x52584, 0x52a5a, 0x59a10
LINK_SPEED, SPEED_SET, PORT_BASE, SYNC = 0x52a5e, 0x52a60, 0x52a62, 0x52a7e
MODEM_BAUD, MODEM_PORT, MODEM_IRQ = 0x52990, 0x52994, 0x52996
SER_BAUD, SER_PORT, SER_IRQ = 0x52a52, 0x52a56, 0x52a58
UART_BUF, IRQ_BUF, VEC_TBL, UART, FIFO = 0x59a60, 0x59a64, 0x59a6c, 0x59a70, 0x59a7c


EXTRA = {
    "IpxInstalled_": 0x1DCA0, "IpxOpenSocket_": 0x1DCE0,
    "IpxCloseSocket_": 0x1DD20, "IpxListen_": 0x1DDD0,
    "IpxSend_": 0x1DE14, "IpxRelinquish_": 0x1DDA0,
    "IpxSetup_": 0x1DD5C, "NetAllocReal_": 0x23D10,
    "NetResizeReal_": 0x23D88, "NetFreeReal_": 0x23DD8,
}


def _flat_clib_stubs():
    def _fmemset(e, log):
        dst, c, n = e.reg("eax"), e.reg("ebx") & 0xFF, e.reg("ecx")
        if n:
            e.write(dst, bytes([c]) * n)
        return dst

    def _fmemcpy(e, log):
        dst, src, n = e.reg("eax"), e.reg("ebx"), e.u32(e.reg("esp") + 4)
        if n:
            e.write(dst, e.read(src, n))
        return dst

    def _fmemcmp(e, log):
        a, b, n = e.reg("eax"), e.reg("ebx"), e.u32(e.reg("esp") + 4)
        x, y = e.read(a, n), e.read(b, n)
        return 0 if x == y else (1 if x > y else 0xFFFFFFFF)

    def _strlen(e, log):
        return len(e.cstr(e.reg("eax"), 256))

    return [
        T4Stub(0x33B41, fn=_fmemset),
        T4Stub(0x34988, fn=_fmemcpy, stack_pop=4),
        T4Stub(0x34963, fn=_fmemcmp, stack_pop=4),
        T4Stub(0x31D1A, fn=_strlen),
    ]


def _init(e):
    e.uc.mem_map(0x80000, 0x10000)
    e.alloc(16, 16)
    e.alloc(0x900, 16)
    e.alloc(256, 16)
    e.alloc(0x2000, 16)


def _layout():
    e = Emu()
    P = {}
    P["blk"] = e.alloc(16, 16)
    P["st"] = e.alloc(0x900, 16)
    P["rx"] = e.alloc(256, 16)
    P["aux"] = e.alloc(0x2000, 16)
    return P


def _w(e, a, v, n):
    e.write(a, (v & ((1 << (8 * n)) - 1)).to_bytes(n, "little"))


def _rd(e, a, n=4):
    return int.from_bytes(bytes(e.read(a, n)), "little")


def _blk(e, L, seg=0x1234, buf=True):
    _w(e, L["blk"], L["st"], 4)
    _w(e, L["blk"] + 4, 0x10, 2)
    _w(e, L["blk"] + 8, seg, 2)
    _w(e, IPX_BUF, L["blk"] if buf else 0, 4)


def _go(src, name, addr, cases, stubs, watch, L, **kw):
    kw.setdefault("extra", EXTRA)
    all_stubs = list(stubs) + _flat_clib_stubs()
    t4spec.run_spec(D + src, name, addr, cases, stubs=all_stubs, watch=watch,
                    init_emu=_init, **kw)


def _ipxwatch(L):
    return [(L["st"], 0x900), (L["blk"], 16), (IPX_BUF, 4), (ERR_TEXT, 0x38)]


def test_net_ipx_start():
    L = _layout()

    def mk(inst, sock):
        return [
            T4Stub(0x23d10, fn=lambda e, log: (log(e.reg("eax")), L["blk"])[1],
                   log_regs=("eax",)),
            T4Stub(0x23d88, log_regs=("eax", "edx")),
            T4Stub(0x23dd8, log_regs=("eax",)),
            T4Stub(0x1dca0, ret=inst, log_regs=()),
            T4Stub(0x1dce0, ret=sock, log_regs=("eax",)),
            T4Stub(0x1dd5c, log_regs=("eax", "edx")),
            T4Stub(0x1ddd0, log_regs=("eax", "edx")),
        ]

    def fresh(e):
        _blk(e, L, buf=False)
        _w(e, L["st"] + 2, 0xdeadbeef, 4)

    def pre(e):
        _blk(e, L)
        _w(e, L["st"] + 2, 0x11223344, 4)
    w = _ipxwatch(L)
    for inst, sock in ((1, 0x4567), (0, 0), (1, 0)):
        _go("net_ipx_start_reference.c", "NetIpxStart_", 0x1f050,
            [T4Case(setup=fresh, label="fresh"), T4Case(setup=pre, label="pre")],
            mk(inst, sock), w, L)


def test_net_ipx_connect():
    L = _layout()

    def stubs():
        return [
            T4Stub(0x1f424, log_regs=("eax", "edx"),
                   fn=lambda e, log: (log(e.reg("eax"), e.reg("edx")),
                                      _rd(e, L["aux"]))[1]),
            T4Stub(0x1f580, fn=lambda e, log: (log(e.reg("ebx"), int.from_bytes(e.read(e.reg("eax"), 4), "little")), 0)[1]),
            T4Stub(0x1f564, log_regs=()),
            T4Stub(0x34949, log_regs=("eax",)),
        ]

    def base(e):
        _blk(e, L)
        _w(e, NODE_NUM, 0x0102, 2)
        e.write(SIG, b"WARCRAFT\0\0")
        _w(e, KEY1, 0, 2)
        _w(e, KEY46, 0, 2)
        _w(e, L["aux"], 0, 4)
        e.write(L["st"] + 0x72, b"WARCRAFT\0\0" + b"\x02\x01")

    def abort1(e):
        base(e)
        _w(e, KEY1, 1, 2)

    def abort46(e):
        base(e)
        _w(e, KEY46, 5, 2)

    def ok(peer):
        def f(e):
            base(e)
            _w(e, L["aux"], 1, 4)
            _w(e, L["st"] + 0x1c, peer, 2)
        return f
    w = _ipxwatch(L) + [(L["aux"], 4)]
    _go("net_ipx_connect_reference.c", "NetIpxConnect_", 0x1f230,
        [T4Case(setup=abort1, label="abort1"), T4Case(setup=abort46, label="abort46"),
         T4Case(setup=ok(0xb), label="ok-peer-b"), T4Case(setup=ok(0), label="ok-peer-0")],
        stubs(), w, L)


def test_net_ipx_stop():
    L = _layout()
    stubs = [T4Stub(0x1dd20, log_regs=("eax",)), T4Stub(0x23dd8, log_regs=("eax",))]

    def nobuf(e):
        _blk(e, L, buf=False)

    def sock(v):
        def f(e):
            _blk(e, L)
            _w(e, L["st"], v, 2)
        return f
    _go("net_ipx_stop_reference.c", "NetIpxStop_", 0x1f3c8,
        [T4Case(setup=nobuf, label="nobuf"), T4Case(setup=sock(0), label="nosock"),
         T4Case(setup=sock(0x4567), label="sock"), T4Case(setup=sock(0xffff), label="ffff")],
        stubs, _ipxwatch(L), L, out_regs=())


def test_net_ipx_receive():
    L = _layout()
    st = L["st"]

    def ecb(i):
        return st + 0x22 + i * 0xd0

    def setup(slots):
        def f(e):
            _blk(e, L)
            e.write(st + 6, b"\xaa\xbb\xcc\xdd\xee\xff")
            e.write(L["rx"], b"\x55" * 64)
            for i in range(1, 10):
                _w(e, ecb(i) + 8, 1, 1)
            for i, (pid, ln, own) in slots.items():
                _w(e, ecb(i) + 8, 0, 1)
                e.write(ecb(i) + 0x1c, b"\xaa\xbb\xcc\xdd\xee\xff" if own else b"\x01" * 6)
                _w(e, ecb(i) + 0x48, pid, 4)
                _w(e, ecb(i) + 0x4c, 0x0c0c + i, 2)
                _w(e, ecb(i) + 0x4e, ln, 2)
                e.write(ecb(i) + 0x3c, bytes(range(i, i + 12)))
                e.write(ecb(i) + 0x50, bytes(range(0x30 + i, 0x30 + i + ln)))
        return f
    def listen(e, log):
        seg, off = e.reg("eax"), e.reg("edx")
        log(seg, off)
        # Re-arm the ECB matching (off & 0xffff) so own-packet drops don't loop
        for i in range(1, 10):
            if (ecb(i) & 0xffff) == (off & 0xffff):
                _w(e, ecb(i) + 8, 1, 1)
                break
        return 0
    stubs = [T4Stub(0x1dda0, log_regs=()), T4Stub(0x1ddd0, fn=listen)]
    w = _ipxwatch(L) + [(L["rx"], 64)]
    cases = [
        T4Case(args=(L["rx"], 0), setup=setup({}), label="empty"),
        T4Case(args=(L["rx"], 0), setup=setup({3: (0xfffffff0, 5, False)}), label="one"),
        T4Case(args=(L["rx"], 0), setup=setup(
            {2: (0xfffffff0, 4, False), 7: (0xfffffff5, 6, False)}), label="two"),
        T4Case(args=(L["rx"], 0), setup=setup({4: (0xfffffff0, 4, True)}), label="own"),
        T4Case(args=(L["rx"], 0), setup=setup({9: (0xfffffff0, 0, False)}), label="zerolen"),
    ]
    _go("net_ipx_receive_reference.c", "NetIpxReceive_", 0x1f424, cases, stubs, w, L)


def test_net_ipx_send():
    L = _layout()
    st = L["st"]

    def setup(busy, pid, cmd):
        def f(e):
            _blk(e, L)
            _w(e, st + 0x2a, busy, 1)
            _w(e, st + 0x1e, pid, 4)
            _w(e, st + 0x1a, cmd, 2)
            e.write(L["rx"], bytes(range(1, 65)))
        return f

    def relinq(e, log):
        log()
        _w(e, st + 0x2a, 0, 1)
    stubs = [T4Stub(0x1dda0, fn=relinq, log_regs=()),
             T4Stub(0x1de14, log_regs=("eax", "edx"))]
    cases = [
        T4Case(args=(L["rx"], 0, 12), setup=setup(0, 0xffffffff, 0xa), label="idle"),
        T4Case(args=(L["rx"], 0, 12), setup=setup(1, 0xfffffff0, 0xb), label="busy"),
        T4Case(args=(L["rx"], 0, 0), setup=setup(0, 1, 0xc), label="len0"),
        T4Case(args=(L["rx"], 0, 40), setup=setup(0, 0, 0xc), label="wrap"),
    ]
    _go("net_ipx_send_reference.c", "NetIpxSend_", 0x1f580, cases, stubs,
        _ipxwatch(L) + [(L["rx"], 64)], L, out_regs=())


def test_net_serial_connect():
    L = _layout()
    aux = L["aux"]
    msgs = [b"listen\0", b"talk\0", b"ack\0"]

    def recv(e, log):
        log(e.reg("edx"))
        sel = _rd(e, aux, 1)
        if sel == 0xff:
            return 0
        e.write(e.reg("eax"), msgs[sel])
        return 1

    def send(e, log):
        n = e.reg("ebx")
        s = e.read(e.reg("eax"), min(n, 16))
        log(int.from_bytes(s[:4], "little"), n)
        return 0

    def stubs(dial=0, answer=0):
        return [
            T4Stub(0x1fb54, log_regs=()),
            T4Stub(0x1fbc8, fn=recv),
            T4Stub(0x1fd30, fn=send),
            T4Stub(0x20884, ret=dial, log_regs=()),
            T4Stub(0x208d4, ret=answer, log_regs=()),
            T4Stub(0x30e98, ret=0, log_regs=()),
            T4Stub(0x31784, log_regs=("eax",)),
        ]

    def setup(modem=0, camp=0, sel=0, k1=0, k46=0, resp=b"BUSY\0"):
        def f(e):
            _w(e, MODEM_LINK, modem, 2)
            _w(e, OWN_CAMP, camp, 2)
            _w(e, aux, sel, 1)
            _w(e, KEY1, k1, 2)
            _w(e, KEY46, k46, 2)
            e.write(NET_RESP, resp)
        return f
    w = [(aux, 4)]
    cases = [
        T4Case(setup=setup(sel=0), label="listen"),
        T4Case(setup=setup(sel=1), label="talk"),
        T4Case(setup=setup(sel=2), label="ack"),
        T4Case(setup=setup(sel=0xff, k1=1), label="abort"),
        T4Case(setup=setup(sel=0, k46=3), label="abort46"),
        T4Case(setup=setup(modem=1, camp=0, sel=1), label="answer-fail"),
        T4Case(setup=setup(modem=1, camp=1, sel=1, resp=b"ERROR\0"), label="dial-fail"),
    ]
    _go("net_serial_connect_reference.c", "NetSerialConnect_", 0x1f62c, cases,
        stubs(), w, L)
    _go("net_serial_connect_reference.c", "NetSerialConnect_", 0x1f62c, cases,
        stubs(dial=1, answer=1), w, L)


def test_net_serial_start():
    L = _layout()
    RM_UART = 0x80000
    RM_VEC = 0x84000
    stubs = [
        T4Stub(0x23d10, fn=lambda e, log: (log(e.reg("eax")), L["blk"])[1],
               log_regs=("eax",)),
        T4Stub(0x312f0, log_regs=("eax", "edx")),
        T4Stub(0x31870, ret=0x40, log_regs=("eax", "edx")),
        T4Stub(0x31844, ret=0x40, log_regs=("eax", "edx")),
        T4Stub(0x32740, log_regs=("eax", "edx")),
        T4Stub(0x1fe04, log_regs=()),
        T4Stub(0x1fe48, log_regs=()),
    ]

    def setup(pre, modem, sset=0xffff, pb=0xffff, fifo=0, baud=9600):
        def f(e):
            _w(e, L["blk"], RM_UART, 4)
            _w(e, L["blk"] + 8, RM_UART >> 4, 2)
            _w(e, UART_BUF, L["blk"] if pre else 0, 4)
            _w(e, IRQ_BUF, L["blk"] if pre else 0, 4)
            _w(e, UART, RM_UART, 4)
            _w(e, VEC_TBL, RM_VEC, 4)
            e.write(RM_UART, b"\x77" * 0x1080)
            e.write(RM_VEC, b"\x00" * 0x100)
            _w(e, MODEM_LINK, modem, 2)
            _w(e, MODEM_BAUD, 2400, 4)
            _w(e, MODEM_PORT, 0x3f8, 2)
            _w(e, MODEM_IRQ, 4, 2)
            _w(e, SER_BAUD, baud, 4)
            _w(e, SER_PORT, 0x2f8, 2)
            _w(e, SER_IRQ, 3, 2)
            _w(e, SPEED_SET, sset, 2)
            _w(e, PORT_BASE, pb, 2)
            _w(e, FIFO, fifo, 1)
            _w(e, LINK_SPEED, 7, 2)
            _w(e, SYNC, 9, 2)
        return f
    w = [(RM_UART, 0x1080), (RM_VEC, 0x20), (UART_BUF, 4), (IRQ_BUF, 4), (UART, 4), (VEC_TBL, 4),
         (LINK_SPEED, 2), (SYNC, 2)]
    cases = [
        T4Case(setup=setup(0, 0), label="fresh-serial"),
        T4Case(setup=setup(1, 1), label="pre-modem"),
        T4Case(setup=setup(1, 0, baud=0x960), label="baud2400"),
        T4Case(setup=setup(1, 0, baud=115200), label="fast"),
        T4Case(setup=setup(1, 0, sset=1, pb=0, fifo=1), label="noset"),
        T4Case(setup=setup(1, 0, baud=19200, fifo=0), label="sync"),
    ]
    _go("net_serial_start_reference.c", "NetSerialStart_", 0x1f854, cases, stubs, w, L)


def test_net_serial_stop():
    L = _layout()
    stubs = [T4Stub(0x2094c, log_regs=()), T4Stub(0x200e8, log_regs=())]

    def setup(modem, sset, pb):
        def f(e):
            _w(e, MODEM_LINK, modem, 2)
            _w(e, SPEED_SET, sset, 2)
            _w(e, PORT_BASE, pb, 2)
            _w(e, LINK_SPEED, 5, 2)
            _w(e, SYNC, 6, 2)
        return f
    w = [(MODEM_LINK, 2), (LINK_SPEED, 2), (SYNC, 2)]
    cases = [T4Case(setup=setup(m, s, p), label=f"{m}{s}{p}")
             for m, s, p in ((0, 0, 0), (1, 0xffff, 0xffff), (1, 1, 0xffff), (0, 0xffff, 3))]
    _go("net_serial_stop_reference.c", "NetSerialStop_", 0x1fb0c, cases, stubs, w, L,
        out_regs=())
