/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x1f424 NetIpxReceive (docs/subsystems/network.md).
 * Verified differentially by tests/test_network.py (T4). */
#include <string.h>
#include "network.h"

extern void IpxRelinquishControl(void);

/* 0x1f424: deliver the oldest finished packet (highest id) of the nine
 * receive ECBs and re-arm its slot; 0 when nothing is ready. */
unsigned short NetIpxReceive(void __far *msg)
{
    RmBlock *blk;
    NetIpxState __far *st;
    NetEcb __far *ecb = 0;
    NetPacket __far *p;
    unsigned long best = 0;
    short i;

    IpxRelinquishControl();
    for (i = 1; i < NET_ECB_COUNT; i++) {
        blk = (RmBlock *)net_ipx_buf;
        st = (NetIpxState __far *)blk->base;
        if (st->ecb[i].inuse != 0)
            continue;
        if (_fmemcmp(st->ecb[i].node, st->node, 6) == 0) {
            /* our own packet: drop it and listen again */
            IpxListen(blk->seg,
                      (unsigned short)((unsigned long)&st->ecb[i] & 0xffff));
            continue;
        }
        p = (NetPacket __far *)st->ecb[i].data;
        if (p->id >= best) {
            best = p->id;
            ecb = &st->ecb[i];
        }
    }
    if (best == 0)
        return 0;
    blk = (RmBlock *)net_ipx_buf;
    st = (NetIpxState __far *)blk->base;
    p = (NetPacket __far *)ecb->data;
    _fmemcpy(st->rx_header, p->header, 12);
    st->peer_cmd = p->cmd;
    _fmemcpy(msg, p->payload, p->length);
    IpxListen(blk->seg, (unsigned short)((unsigned long)ecb & 0xffff));
    return p->length;
}
