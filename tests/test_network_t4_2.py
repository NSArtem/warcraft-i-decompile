import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

SRC = path("src", "network")
pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(SRC, "net_modem_init_reference.c")),
    reason="network reference C missing")

NET_RESPONSE = 0x59a10
NET_ERROR_TEXT = 0x59ba8
NET_UART = 0x59a70
KEY_A = 0x5a8d6
KEY_B = 0x5a930
INIT1 = 0x52998
INIT2 = 0x529c8
HANGUP = 0x529f8
PHONE = 0x52a28
DIAL_PULSE = 0x52a51
SEL_A = NET_RESPONSE + 0x4e   # scratch selector bytes (past the 0x50 buffer start)
SEL_B = NET_RESPONSE + 0x4f

WATCH = [(NET_RESPONSE, 0x50), (NET_ERROR_TEXT, 0x38)]


def _strstub(addr, sel=None):
    def fn(e, log):
        log(e.read(e.reg("eax"), 1)[0])
        return e.read(sel, 1)[0] if sel else 0
    return T4Stub(addr, fn=fn)


def _wait_stub():
    def fn(e, log):
        c = e.read(e.reg("eax"), 1)[0]
        log(c)
        return e.read(SEL_A if c == ord("R") else SEL_B, 1)[0]
    return T4Stub(0x20900, fn=fn)


def _strncmp_stub():
    def fn(e, log):
        log(e.read(e.reg("eax"), 1)[0], e.read(e.reg("edx"), 1)[0], e.reg("ebx"))
        return e.read(SEL_A, 1)[0]
    return T4Stub(0x30c6f, fn=fn)


def _sel(a, b):
    return {SEL_A: bytes([a]), SEL_B: bytes([b])}


def _case(label, **mem):
    return T4Case(label=label, mem=mem)


def _wait_seq_stub(seq_addr):
    def fn(e, log):
        idx = e.read(seq_addr, 1)[0]
        b = e.read(seq_addr + 1 + idx, 1)[0]
        if b != 0:
            e.write(seq_addr, bytes([idx + 1]))
            return b
        return 0x0a
    return T4Stub(0x201c0, fn=fn)


def _waitcases():
    z = struct.pack("<H", 0)
    nz = struct.pack("<H", 1)
    S = INIT2  # scratch byte stream (cursor at +0, bytes at +1..)
    return [
        T4Case(args=(INIT1,), label="ok match",
               mem={KEY_A: z, KEY_B: z, INIT1: b"OK\0", S: b"\x00OK\r\n\0"}),
        T4Case(args=(INIT1,), label="no carrier",
               mem={KEY_A: z, KEY_B: z, INIT1: b"OK\0", S: b"\x00NO CARRIER\r\n\0"}),
        T4Case(args=(INIT1,), label="busy",
               mem={KEY_A: z, KEY_B: z, INIT1: b"OK\0", S: b"\x00BUSY\r\n\0"}),
        T4Case(args=(INIT1,), label="esc a", mem={KEY_A: nz, KEY_B: z, INIT1: b"OK\0", S: b"\x00\0"}),
        T4Case(args=(INIT1,), label="esc b", mem={KEY_A: z, KEY_B: nz, INIT1: b"OK\0", S: b"\x00\0"}),
    ]


def _strlen_stub():
    def fn(e, log):
        return len(e.cstr(e.reg("eax"), 256))
    return T4Stub(0x31d1a, fn=fn)


def _run_wait(src_name):
    t4spec.run_spec(
        os.path.join(SRC, src_name), "NetModemWaitResponse_", 0x20900,
        _waitcases(), watch=WATCH + [(INIT2, 24)],
        stubs=[_wait_seq_stub(INIT2), _strlen_stub()])


def test_net_modem_wait_response_tail():
    _run_wait("net_modem_wait_response_reference.c")


def test_net_modem_wait_response():
    _run_wait("net_modem_wait_response_reference.c")


def test_net_modem_init():
    def m(i1, i2, a, b, extra=None):
        d = _sel(a, b)
        d[INIT1] = i1
        d[INIT2] = i2
        d[NET_RESPONSE] = b"ERROR\0"
        return d
    cases = [
        T4Case(mem=m(b"\0", b"\0", 0, 1), label="both empty"),
        T4Case(mem=m(b"ATZ\0", b"AT\0", 0, 0), label="init1 fail, strncmp eq"),
        T4Case(mem=m(b"ATZ\0", b"AT\0", 1, 0), label="init1 fail, strncmp ne"),
        T4Case(mem=m(b"\0", b"AT\0", 0, 1), label="init2 fail, copy"),
        T4Case(mem=m(b"ATZ\0", b"AT\0", 1, 1), label="init2 fail ne"),
    ]
    # WaitResponse returns SEL_B; strncmp returns SEL_A
    cases[1].mem.update(_sel(0, 0))
    cases[2].mem.update(_sel(1, 0 + 0))
    t4spec.run_spec(
        os.path.join(SRC, "net_modem_init_reference.c"), "NetModemInit_", 0x207c0,
        cases, watch=WATCH,
        stubs=[_strstub(0x206c8), _strstub(0x20900, SEL_B), _strncmp_stub(),
               T4Stub(0x31784, log_regs=("eax",))])


def _dial_stubs():
    def sp(e, log):
        esp = e.reg("esp")
        fmt = struct.unpack("<I", e.read(esp + 8, 4))[0]
        log(e.read(fmt + 3, 1)[0])
        return 0
    return [_strstub(0x207c0, SEL_A) if False else T4Stub(
                0x207c0, fn=lambda e, log: (log(), e.read(SEL_A, 1)[0])[1]),
            T4Stub(0x31be2, fn=sp),
            T4Stub(0x206c8, log_regs=()),
            _strstub(0x20900, SEL_B)]


def test_net_modem_dial():
    def c(label, init, pulse, conn):
        return T4Case(label=label, mem={
            SEL_A: bytes([init]), SEL_B: bytes([conn]),
            DIAL_PULSE: bytes([pulse]), PHONE: b"555\0"})
    t4spec.run_spec(
        os.path.join(SRC, "net_modem_dial_reference.c"), "NetModemDial_", 0x20884,
        [c("init fail", 0, 0, 1), c("tone ok", 1, 0, 1),
         c("pulse ok", 1, 1, 1), c("pulse nocon", 1, 1, 0)],
        stubs=_dial_stubs())


def test_net_modem_answer():
    def c(label, init, ring, conn):
        return T4Case(label=label, mem={SEL_A: bytes([ring]), SEL_B: bytes([conn])},
                      setup=None)
    # Init stub keyed on SEL_A would clash with RING; use dedicated byte
    init_sel = NET_RESPONSE + 0x4d

    def cc(label, init, ring, conn):
        d = _sel(ring, conn)
        d[init_sel] = bytes([init])
        return T4Case(label=label, mem=d)
    t4spec.run_spec(
        os.path.join(SRC, "net_modem_answer_reference.c"), "NetModemAnswer_", 0x208d4,
        [cc("init fail", 0, 1, 1), cc("no ring", 1, 0, 1),
         cc("answered", 1, 1, 1), cc("no connect", 1, 1, 0)],
        stubs=[T4Stub(0x207c0, log_regs=(),
                      fn=lambda e, log: (log(), e.read(init_sel, 1)[0])[1]),
               _wait_stub(), _strstub(0x206c8)])


def test_net_modem_hangup():
    def setup_for(io):
        def s(emu):
            u = emu.alloc(16, 4)
            emu.write(u, struct.pack("<H", io))
            emu.write(NET_UART, struct.pack("<I", u))
        return s
    cases = [T4Case(label="com1", setup=setup_for(0x3f8),
                    mem={HANGUP: b"AT H0\0"}),
             T4Case(label="com2", setup=setup_for(0x2f8),
                    mem={HANGUP: b"ATH\0"}),
             T4Case(label="com3", setup=setup_for(0x3e8),
                    mem={HANGUP: b"\0"})]
    t4spec.run_spec(
        os.path.join(SRC, "net_modem_hangup_reference.c"), "NetModemHangup_", 0x2094c,
        cases, out_regs=(),
        stubs=[T4Stub(0x349b0, ret=0x5a, log_regs=("eax",)),
               T4Stub(0x349bc, log_regs=("eax", "edx")),
               T4Stub(0x31784, log_regs=("eax",)),
               _strstub(0x206c8),
               T4Stub(0x201c0, ret=0xFFFFFFFF, log_regs=())])
