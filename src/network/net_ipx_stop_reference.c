/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* REFERENCE C for 0x1f3c8 NetIpxStop (docs/subsystems/network.md).
 * Verified differentially by tests/test_network.py (T4); the IPX wrappers it
 * calls have no symbol-database entries yet. */
#include "network.h"
#include "dos_realmode_mem_f1.h"

void NetIpxStop(void)
{
    NetIpxState __far *st;

    if (net_ipx_buf == 0)
        return;
    st = (NetIpxState __far *)((RmBlock *)net_ipx_buf)->base;
    if (st->socket != 0) {
        IpxCloseSocket(st->socket);
        st = (NetIpxState __far *)((RmBlock *)net_ipx_buf)->base;
        st->socket = 0;
    }
    if (net_ipx_buf != 0) {
        st = (NetIpxState __far *)((RmBlock *)net_ipx_buf)->base;
        st->socket = 0;
        RealModeFree(net_ipx_buf);
        net_ipx_buf = 0;
    }
}
