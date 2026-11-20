import os
import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub, run_spec

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM")

SRC = lambda n: path("src", "network", n)

NET_UART = 0x59A70
G_IRQ_BUF, G_OLD_ISR_OFF, G_VEC_TABLE = 0x59A64, 0x59A68, 0x59A6C
G_OLD_VEC_SEG, G_OLD_ISR_SEL, G_IRQ_VEC, G_OLD_VEC_OFF, G_FIFO = 0x59A74, 0x59A76, 0x59A78, 0x59A7A, 0x59A7C
RX_LEN, RX_ESC, RX_DONE = 0x52A74, 0x52A76, 0x52A78
NET_CR = 0x570F4
USZ = 0x1100
SEQ = 0x300


def _w(emu, addr, size, val):
    emu.write(addr, (val & ((1 << (8 * size)) - 1)).to_bytes(size, "little"))


def _run(src, name, addr, mk, stubs=(), watch=(), out_regs=(), log_cap=1024):
    cases, w = [], list(watch)

    def init(emu):
        U = emu.alloc(USZ, 16)
        B = emu.alloc(0x400, 16)
        w.append((U, USZ))
        w.append((B, 0x400))
        cases.extend(mk(U, B))

    run_spec(SRC(src), name, addr, cases, watch=w, stubs=stubs,
             out_regs=out_regs, init_emu=init, log_cap=log_cap)


def C(U, B, label, args=(), f=None, g=None, mem=None, seq=()):
    """Case: uart fields f{off:(size,val)}, globals g{addr:(size,val)}, B-memory mem{off:bytes}."""
    def setup(emu):
        emu.write(U, bytes(USZ))
        emu.write(B, bytes(0x400))
        _w(emu, NET_UART, 4, U)
        _w(emu, G_IRQ_BUF, 4, B + 0x100)
        _w(emu, G_VEC_TABLE, 4, B + 0x200)
        for off, d in (mem or {}).items():
            emu.write(B + off, d)
        if seq:
            emu.write(B + SEQ + 4, bytes(seq))
        for off, (sz, v) in (f or {}).items():
            _w(emu, U + off, sz, v)
        for a, (sz, v) in (g or {}).items():
            _w(emu, a, sz, v)
    return T4Case(args=args(B) if callable(args) else args, setup=setup, label=label)


def _inp_seq(B_holder):
    def fn(e, log):
        cell = B_holder[0] + SEQ
        idx = int.from_bytes(e.read(cell, 4), "little")
        log(e.reg("eax"))
        e.write(cell, (idx + 1).to_bytes(4, "little"))
        return e.read(cell + 4 + idx, 1)[0] if idx < 32 else 1
    return fn


def _seq_stubs(mk):
    """Wrap case maker so the sequence stub knows the B buffer address."""
    holder = [0]

    def mk2(U, B):
        holder[0] = B
        return mk(U, B)
    return holder, mk2


IO = {0: (2, 0x3F8), 2: (2, 4)}


def _rx(data, **extra):
    f = dict(IO)
    f.update({0xA: (2, len(data)), 0xC: (2, 0), 0xE: (2, len(data))})
    return f


def test_net_serial_receive():
    def mk(U, B):
        def rxf(data, cnt=None):
            f = dict(IO)
            f.update({0xA: (2, len(data)), 0xC: (2, 0), 0xE: (2, len(data) if cnt is None else cnt)})
            for i, b in enumerate(data):
                f[0x10 + i] = (1, b)
            return f
        far = (B, 0)
        return [
            C(U, B, "empty", (B + 0x40, 0x10), rxf(b"")),
            C(U, B, "plain-then-end", (B + 0x40, 0x10), rxf(b"AB\x70\x00")),
            C(U, B, "escaped-0x70", (B + 0x40, 0x10), rxf(b"A\x70\x70B\x70\x00")),
            C(U, B, "overrun", (B + 0x40, 0x10), rxf(b"AB", 0x7FD)),
            C(U, B, "done-reset", (B + 0x40, 0x10), rxf(b"Z"), g={RX_DONE: (2, 1), RX_LEN: (2, 5)}),
            C(U, B, "too-long", (B + 0x40, 0x10), rxf(b"A" * 20 + b"\x70\x00"), g={RX_LEN: (2, 0x88)}),
        ]
    _run("net_serial_receive.c", "NetSerialReceive_", 0x1FBC8, mk,
         stubs=[T4Stub(0x349B8, log_regs=()), T4Stub(0x349BA, log_regs=())],
         watch=[(RX_LEN, 6)], out_regs=("eax",))


def test_net_serial_send():
    def mk(U, B):
        def m(data):
            return {0x40: data}
        return [
            C(U, B, "plain", (B + 0x40, 0x10, 3), mem=m(b"abc"), f={0x1066: (4, 99)}),
            C(U, B, "escape", (B + 0x40, 0x10, 4), mem=m(b"a\x70\x70b"), f={0x1066: (4, 99)}),
            C(U, B, "zero-len", (B + 0x40, 0x10, 0), f={0x1066: (4, 99)}),
            C(U, B, "too-long", (B + 0x40, 0x10, 0x89), f={0x1072: (4, 3)}),
            C(U, B, "too-long-larger", (B + 0x40, 0x10, 0x89), f={0x1072: (4, 0x200)}),
            C(U, B, "max", (B + 0x40, 0x10, 0x88), mem=m(b"\x70" * 0x88), f={0x1062: (4, 0x100)}),
        ]
    _run("net_serial_send.c", "NetSerialSend_", 0x1FD30, mk,
         stubs=[T4Stub(0x1FB60, log_regs=("eax", "edx"))],
         watch=[(0x59A7D, 0x90)])


def test_net_serial_uart_init():
    def mk(U, B):
        base = dict(IO)
        base[6] = (4, 0x2580)
        return [
            C(U, B, "default", (), base),
            C(U, B, "baud-3840", (), {**base, 6: (4, 0x3840)}),
            C(U, B, "old-set", (), base, g={G_OLD_ISR_OFF: (4, 0x1234), G_OLD_VEC_OFF: (2, 0x55)}),
            C(U, B, "irq7", (), {**base, 2: (2, 7)}),
        ]
    def int386_stub(e, log):
        import struct as _st
        intno = e.reg("eax") & 0xFF
        inp, outp = e.reg("edx"), e.reg("ebx")
        r = bytearray(e.read(inp, 0x1C))
        fn = _st.unpack_from("<I", r, 0)[0] & 0xFFFF
        bl = _st.unpack_from("<I", r, 4)[0] & 0xFF
        cx = _st.unpack_from("<I", r, 8)[0] & 0xFFFF
        dx = _st.unpack_from("<I", r, 0xC)[0]
        # 0x204/0x200 are GET calls (cx/dx are outputs, uninitialized on input);
        # 0x205 sets handler (edx differs between orig and C); 0x201 sets RM vector (all inputs)
        if fn in (0x204, 0x200):
            log(intno, fn, bl)
        elif fn == 0x205:
            log(intno, fn, bl, cx)
        else:
            log(intno, fn, bl, cx, dx)
        if intno == 0x31 and fn == 0x0204:
            _st.pack_into("<I", r, 8, (_st.unpack_from("<I", r, 8)[0] & 0xFFFF0000) | 0x1234)
            _st.pack_into("<I", r, 0xC, 0x5678)
        elif intno == 0x31 and fn == 0x0200:
            _st.pack_into("<I", r, 8, (_st.unpack_from("<I", r, 8)[0] & 0xFFFF0000) | 0x00C0)
            _st.pack_into("<I", r, 0xC, (_st.unpack_from("<I", r, 0xC)[0] & 0xFFFF0000) | 0x0100)
        if outp:
            e.write(outp, bytes(r))
        return 0
    for ret in (0xC1, 0x01):
        _run("net_serial_uart_init_reference.c", "NetSerialUartInit_", 0x1FE48, mk,
             stubs=[T4Stub(0x349B0, ret=ret, log_regs=("eax",)),
                    T4Stub(0x349BC, log_regs=("eax", "edx")),
                    T4Stub(0x349CA, fn=int386_stub),
                    T4Stub(0x349B8, log_regs=()), T4Stub(0x349BA, log_regs=())],
             watch=[(G_IRQ_BUF, 0x1E)])


def test_net_serial_uart_stop():
    def mk(U, B):
        return [
            C(U, B, "basic", (), dict(IO), g={G_IRQ_VEC: (2, 0xC), G_OLD_VEC_SEG: (2, 0x70), G_OLD_VEC_OFF: (2, 0x80)}),
            C(U, B, "isr", (), {0: (2, 0x2F8), 2: (2, 3)}, g={G_OLD_ISR_SEL: (2, 0x1F), G_OLD_ISR_OFF: (4, 0x5000)}),
            C(U, B, "zero", (), dict(IO)),
        ]
    _run("net_serial_uart_stop_reference.c", "NetSerialUartStop_", 0x200E8, mk,
         stubs=[T4Stub(0x349B0, ret=0x10, log_regs=("eax",)),
                T4Stub(0x349BC, log_regs=("eax", "edx")),
                T4Stub(0x349CA, log_regs=("eax", "edx", "ebx"))])


def test_net_serial_push_bytes():
    def mk(U, B):
        return [
            C(U, B, "simple", (B + 0x40, 4), mem={0x40: b"wxyz"}, f={0x810: (2, 10), 0x814: (2, 3)}),
            C(U, B, "empty", (B + 0x40, 0), f={0x810: (2, 10)}),
            C(U, B, "wrap-exact", (B + 0x40, 4), mem={0x40: b"wxyz"}, f={0x810: (2, 0x7FC)}),
            C(U, B, "wrap-past", (B + 0x40, 5), mem={0x40: b"vwxyz"}, f={0x810: (2, 0x7FE)}),
            C(U, B, "last-fit", (B + 0x40, 3), mem={0x40: b"abc"}, f={0x810: (2, 0x7FC)}),
        ]
    _run("net_serial_push_bytes.c", "NetSerialPushBytes_", 0x20258, mk,
         stubs=[T4Stub(0x2020C, log_regs=("eax",)),
                T4Stub(0x34988, log_regs=("eax", "edx", "ebx", "ecx"), stack_pop=4)])


def _isr_test(src, name, addr, seqs):
    holder = [0]

    def mk(U, B):
        holder[0] = B
        f = dict(IO)
        f.update({0xA: (2, 0x7FF), 0xE: (2, 1), 0x814: (2, 3), 0x812: (2, 0x7FF),
                  0x816 + 0x7FF: (1, 0x5A), 0x816: (1, 0x11), 0x817: (1, 0x22), 0x818: (1, 0x33),
                  0x1018: (1, 0)})
        return [C(U, B, lbl, (), f, seq=s) for lbl, s in seqs]

    cases, w = [], []

    def init(emu):
        U = emu.alloc(USZ, 16)
        B = emu.alloc(0x400, 16)
        w.append((U, USZ))
        w.append((B, 0x400))
        cases.extend(mk(U, B))

    stubs = [T4Stub(0x34850, log_regs=()),
             T4Stub(0x349B0, log_regs=("eax",), fn=_inp_seq(holder)),
             T4Stub(0x349BC, log_regs=("eax", "edx"))]
    run_spec(SRC("net_serial_isr.c"), name, addr, cases, watch=w, stubs=stubs,
             out_regs=(), init_emu=init, interrupt=True)


def test_net_serial_isr():
    _isr_test("net_serial_isr.c", "NetSerialIsr_", 0x202C0, [
        ("none", [1]),
        ("rx", [4, 0x41, 1]),
        ("rx-wrap", [4, 0x42, 1]),
        ("tx", [2, 1]),
        ("line-status", [6, 0x1E, 1]),
        ("unknown", [0]),
    ])


def test_net_serial_isr_fifo():
    _isr_test("net_serial_isr.c", "NetSerialIsrFifo_", 0x20448, [
        ("none", [1]),
        ("rx-fifo", [4, 0x41, 1, 0x42, 0, 1]),
        ("tx-fifo", [2, 1]),
        ("line-status", [6, 0x1E, 1]),
    ])


def test_net_modem_command():
    def mk(U, B):
        return [
            C(U, B, "empty", (B + 0x40,), mem={0x40: b"\x00"}),
            C(U, B, "one", (B + 0x40,), mem={0x40: b"A\x00"}),
            C(U, B, "atz", (B + 0x40,), mem={0x40: b"ATZ\x00"}),
            C(U, B, "long", (B + 0x40,), mem={0x40: b"ATDT5551212\x00"}),
        ]
    _run("net_modem_command.c", "NetModemCommand_", 0x206C8, mk,
         stubs=[T4Stub(0x1FB60, log_regs=("eax", "edx")),
                T4Stub(0x31784, log_regs=("eax",)),
                T4Stub(0x31D1A, fn=lambda e, log: len(e.cstr(e.reg("eax"), 256)))])
