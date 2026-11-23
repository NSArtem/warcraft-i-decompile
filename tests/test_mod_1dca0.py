import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_1dca0')
CALLEE = 0x23e50


def test_t3_files_match():
    t4spec.assert_t3_matches(SRC, ['ipx_close_socket_reference.c', 'ipx_get_internetwork_address_reference.c',
                                   'ipx_installed_reference.c', 'ipx_listen_reference.c',
                                   'ipx_open_socket_reference.c', 'ipx_relinquish_control_reference.c',
                                   'ipx_send_packet_reference.c'])


def _make_stub(state):
    def fn(e, log):
        ptr = e.reg('edx')
        data = e.read(ptr, 0x32)
        dws = struct.unpack('<8I', data[:32])
        ws = struct.unpack('<9H', data[32:50])
        log(e.reg('eax'), *dws, *ws)
        e.write(ptr + 0x1c, struct.pack('<I', state[0]))
        e.write(ptr + 0x14, struct.pack('<I', state[1]))
        return 0
    return fn


def _run(fname, link, addr, cases, out_regs=("eax",)):
    state = [0, 0]
    cs = []
    for args, ea, ed in cases:
        def setup(e, ea=ea, ed=ed):
            state[0] = ea
            state[1] = ed
        cs.append(T4Case(args=args, setup=setup, label=f"{args}/{ea:#x}/{ed:#x}"))
    t4spec.run_spec(os.path.join(SRC, fname), link, addr, cs,
                    stubs=[T4Stub(CALLEE, fn=_make_stub(state))],
                    out_regs=out_regs)


def test_ipx_installed():
    _run('ipx_installed_reference.c', 'IpxInstalled_', 0x1dca0,
         [((), v, 0) for v in (0xff, 0, 0x12ff, 0xffff, 0x7a00, 0xfe)])


def test_ipx_open_socket():
    _run('ipx_open_socket_reference.c', 'IpxOpenSocket_', 0x1dce0,
         [((s,), 0x55, d) for s, d in ((0, 0), (0x4000, 0x4000), (0x1ffff, 0x1234),
                                       (0xffff, 0xdeadbeef))])


def test_ipx_close_socket():
    _run('ipx_close_socket_reference.c', '_IpxCloseSocket'.lstrip('_') + '_', 0x1dd20,
         [((s,), 0, 0) for s in (0, 1, 0x4000, 0xffff, 0x12345)], out_regs=())


def test_ipx_get_internetwork_address():
    _run('ipx_get_internetwork_address_reference.c', 'IpxGetInternetworkAddress_', 0x1dd5c,
         [((s, o), 0, 0) for s, o in ((0, 0), (0x1234, 0x5678), (0xffff, 0xffff),
                                      (0x12345, 0x98765))], out_regs=())


def test_ipx_relinquish_control():
    _run('ipx_relinquish_control_reference.c', 'IpxRelinquishControl_', 0x1dda0,
         [((), 0, 0), ((), 5, 6)], out_regs=())


def test_ipx_listen():
    _run('ipx_listen_reference.c', 'IpxListen_', 0x1ddd0,
         [((s, o), 0, 0) for s, o in ((0, 0), (0x1234, 0x5678), (0xffff, 0xffff),
                                      (0x12345, 0x98765))], out_regs=())


def test_ipx_send_packet():
    _run('ipx_send_packet_reference.c', 'IpxSendPacket_', 0x1de14,
         [((s, o), 0, 0) for s, o in ((0, 0), (0x1234, 0x5678), (0xffff, 0xffff),
                                      (0x12345, 0x98765))], out_regs=())


def test_exact_tier_by_symbol_entry():
    t4spec.assert_ref_mismatch(SRC, ['ipx_close_socket_reference.c', 'ipx_get_internetwork_address_reference.c', 'ipx_installed_reference.c', 'ipx_listen_reference.c', 'ipx_open_socket_reference.c', 'ipx_relinquish_control_reference.c', 'ipx_send_packet_reference.c'])
