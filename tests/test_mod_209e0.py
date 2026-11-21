import os
import struct

import pytest

from wc1 import t4spec
from wc1 import path
from wc1.emu import Emu

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_209e0')
CHK_ADDR = 0x209e0
BUF = []


def init_emu(emu):
    BUF[:] = [emu.alloc(0x100, 16)]


def _buf_addr():
    probe = Emu()
    init_emu(probe)
    return BUF[0]


STATE = {"ret": 0}


def _driver_addr():
    return t4spec.by_link_lenient()["NetDriverReceiveChecked_"]["addr"]


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_209e0'), ['net_checksum.c', 'net_send_packet_checksummed.c'])


def test_ref_files_still_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_209e0'), ['net_receive_packet_checked_reference.c'])


def _case(ret, word, length, label):
    base = _buf_addr()
    pkt = struct.pack("<HHBB", word, 0x55, length, 0) + bytes(range(16))

    def setup(emu):
        STATE["ret"] = ret

    return t4spec.T4Case(args=(base,), mem={base: pkt.ljust(0x100, b"\0")},
                         setup=setup, label=label)


def test_net_receive_packet_checked():
    def drv(e, log):
        log(e.reg("eax"), e.reg("edx"))
        return STATE["ret"]

    def chk(e, log):
        log(e.reg("eax"), e.reg("edx"))
        return 0x1234

    stubs = [
        t4spec.T4Stub(_driver_addr(), fn=drv),
        t4spec.T4Stub(CHK_ADDR, fn=chk),
    ]
    cases = [
        _case(0, 0x1234, 4, "zero"),
        _case(0xFFFF, 0x1234, 4, "minus1"),
        _case(1, 0x1234, 4, "good"),
        _case(1, 0x1235, 4, "bad_sum"),
        _case(5, 0x1234, 9, "good_len9"),
        _case(5, 0x0000, 0, "bad_len0"),
    ]
    t4spec.run_spec(
        os.path.join(SRC, 'net_receive_packet_checked_reference.c'),
        'NetReceivePacketChecked_', 0x20a14, cases,
        watch=[(_buf_addr(), 16)], stubs=stubs, out_regs=("eax",),
        init_emu=init_emu)
