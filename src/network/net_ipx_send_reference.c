/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x1f580 NetIpxSend (docs/subsystems/network.md).
 * Verified differentially by tests/test_network.py (T4). */
#include <string.h>
#include "network.h"

/* 0x1f580: hand the message to the transmit ECB (slot 0): wait until IPX has
 * completed the previous packet, stamp the decrementing packet id and the
 * command word, copy the payload and send. */
void NetIpxSend(void __far *msg, unsigned len)
{
    RmBlock *blk;
    NetIpxState __far *st;
    NetPacket __far *p;
    unsigned long id;

    for (;;) {
        blk = (RmBlock *)net_ipx_buf;
        st = (NetIpxState __far *)blk->base;
        if (st->ecb[0].inuse == 0)
            break;
        IpxRelinquish();
    }
    id = st->packet_id;
    st->packet_id = id - 1;
    p = (NetPacket __far *)st->ecb[0].data;
    p->id = id;
    p->cmd = st->cmd;
    p->length = (unsigned short)len;
    _fmemcpy(p->payload, msg, len);
    IpxSend(blk->seg, (unsigned short)((unsigned long)&st->ecb[0] & 0xffff));
}
