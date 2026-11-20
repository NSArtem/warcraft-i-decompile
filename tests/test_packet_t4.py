import os
import struct

import pytest

from wc1 import t4spec, path

SRC = path("src", "mod_20c30", "net_send_sync_message_reference.c")

pytestmark = pytest.mark.skipif(not os.path.exists(SRC), reason="reference C missing")


def test_net_send_sync_message():
    holder = []

    def init(emu):
        holder.append(emu.alloc(32, 16))

    def cb(e, log):
        buf = e.reg("edx")
        data = e.read(buf, 0x15)
        # bytes 1..2 of the header are uninitialised stack; skip them
        words = struct.unpack("<IIIII", data[3:3 + 20 - 0] if False else data[3:] + b"\x00\x00")
        log(e.reg("eax"), data[0], *words)
        return 0

    def mk(payload, label):
        return t4spec.T4Case(
            args=(),
            setup=None,
            mem={},
            label=label,
        ), payload

    payloads = {
        "zeros": bytes(18),
        "ones": b"\xff" * 18,
        "ramp": bytes(range(1, 19)),
        "tail": b"\x00" * 16 + b"\x34\x12",
    }
    cases = []

    def init_all(emu):
        init(emu)

    # allocate in init_emu so address is known when building cases
    from wc1.emu import Emu
    probe = Emu()
    init(probe)
    src_addr = holder[0]
    del holder[:]

    for label, p in payloads.items():
        cases.append(t4spec.T4Case(args=(src_addr,), mem={src_addr: p + b"\xaa" * 14},
                                   label=label))

    t4spec.run_spec(
        SRC, "NetSendSyncMessage_", 0x21cb8, cases,
        stubs=[t4spec.T4Stub(0x214d4, log_regs=("eax", "edx"), fn=cb)],
        out_regs=(),
        init_emu=init_all,
    )
