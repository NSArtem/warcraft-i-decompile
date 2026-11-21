import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.emu import Emu

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_20a80')
RECV_PTR = 0x59b9c
SEND_PTR = 0x59ba0
STUB_ADDR = 0x20c1c      # NetDriverDrain body, replaced by a stub
BUF_SIZE = 256
RET_OFF = 0x80
SEG = 0x10

_holder = {}


def _init(emu):
    _holder["buf"] = emu.alloc(BUF_SIZE, 16)


def _buf():
    if "buf" not in _holder:
        _init(Emu())
    return _holder["buf"]


def _counter_addr():
    by = t4spec.by_link_lenient()
    for n in ("_net_sync_counter", "net_sync_counter"):
        if n in by:
            return by[n]["addr"]
    raise AssertionError("net_sync_counter not in symbol DB")


def test_t3_files_match():
    files = ['net_driver_connect_show_cursor.c', 'net_driver_drain.c',
             'net_driver_select.c', 'net_driver_shutdown.c']
    t4spec.assert_t3_matches(path('src/mod_20a80'), files)


def test_reference_files_still_mismatch():
    files = ['net_driver_receive_checked_reference.c',
             'net_driver_send_repeated_reference.c']
    t4spec.assert_ref_mismatch(path('src/mod_20a80'), files)


def _recv_stub_fn(e, log):
    b = _holder["buf"]
    v = struct.unpack("<I", e.read(b + RET_OFF, 4))[0]
    log()
    return v


def test_net_driver_receive_checked():
    b = _buf()

    def case(ret, word1, label):
        data = struct.pack("<HH", 0x1111, word1)
        return t4spec.T4Case(
            args=(b, SEG),
            mem={b: data.ljust(16, b"\0"),
                 b + RET_OFF: struct.pack("<I", ret),
                 RECV_PTR: struct.pack("<I", STUB_ADDR)},
            label=label)

    cases = [
        case(0, 0x1234, "zero"),
        case(0x1234, 0x1234, "match"),
        case(0x1234, 0x4321, "mismatch"),
        case(0x10000, 0x0000, "low word zero"),
        case(0xabcd0005, 0x0005, "high bits, match low"),
        case(0xabcd0005, 0x0006, "high bits, mismatch"),
        case(0xffff, 0xffff, "ffff match"),
        case(1, 0, "one vs zero"),
    ]
    t4spec.run_spec(
        os.path.join(SRC, 'net_driver_receive_checked_reference.c'),
        'NetDriverReceiveChecked_', 0x20ba8, cases,
        watch=[(b, BUF_SIZE)],
        stubs=[t4spec.T4Stub(STUB_ADDR, fn=_recv_stub_fn)],
        init_emu=_init)


def test_net_driver_send_repeated():
    b = _buf()
    ctr = _counter_addr()
    cases = []
    for n in (0, 1, 2, 3, 5):
        for ln in (0, 8, 0x1234, 0xffff):
            cases.append(t4spec.T4Case(
                args=(b, SEG, ln),
                mem={ctr: struct.pack("<H", n),
                     SEND_PTR: struct.pack("<I", STUB_ADDR)},
                label=f"n={n} len={ln:#x}"))
    t4spec.run_spec(
        os.path.join(SRC, 'net_driver_send_repeated_reference.c'),
        'NetDriverSendRepeated_', 0x20bd4, cases,
        watch=[(ctr, 2)],
        stubs=[t4spec.T4Stub(STUB_ADDR, log_regs=("eax", "edx", "ebx"))],
        out_regs=(),
        init_emu=_init)
