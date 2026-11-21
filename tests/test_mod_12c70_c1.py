import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_12c70', 'net_send_message_reference.c')

# Data addresses (from symbol DB)
NET_SEND_STATE = 0x58d94
NET_SEND_SLOT = 0x58d9a
DAT_516AE = 0x516ae
BUF = {'msg': 0x7f000}


def _init(emu):
    try:
        emu.uc.mem_map(0x7f000, 0x1000)
    except Exception:
        pass
    emu.alloc(0x100, 16)


def _case(label, msg_len, flag, campaign, cnt, slot):
    def setup(emu):
        m = BUF['msg']
        emu.write(m, bytes([msg_len, flag]) + b"\x00\x00" +
                  bytes((i * 7 + 3) & 0xff for i in range(0x80)))
        emu.write(DAT_516AE, struct.pack('<h', campaign[0]))
    return T4Case(args=(BUF['msg'],), setup=setup, label=label)


def test_t3_files_still_match():
    t4spec.assert_t3_matches(path('src/mod_12c70'), [])


def test_ref_mismatch_guard():
    t4spec.assert_ref_mismatch(path('src/mod_12c70'), ['net_send_message_reference.c'])


def test_net_send_message():
    cases = [
        _case('plain', 8, 0, (0,), 0, 0),
        _case('flag_set', 16, 0, (1,), 5, 0),
        _case('flag_set2', 4, 0x01, (2,), 9, 0),
    ]
    t4spec.run_spec(
        SRC, 'NetSendMessage_', 0x131d8, cases,
        watch=[(NET_SEND_STATE, 6), (NET_SEND_SLOT, 2)],
        stubs=[T4Stub(0x20a50, log_regs=('eax', 'edx')),
               T4Stub(0x1d000 + 0, log_regs=('eax',))][:1],
        out_regs=('eax',),
        init_emu=_init,
    )
