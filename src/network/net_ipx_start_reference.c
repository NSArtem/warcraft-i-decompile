/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x1f050 NetIpxStart (docs/subsystems/network.md).
 *
 * Not byte-matched yet: NetAllocReal and NetResizeReal still need fixup
 * reconciliation for T3; the T4 harness supplies them through its extra map.
 * Verified differentially by tests/test_network.py.
 */
#include <string.h>
#include "network.h"
#include "dos_realmode_mem_f1.h"

static char ipx_error[53] = "Network driver not found.\nLoad IPX for network play.";

/* 0x1f050: bring the IPX transport up.  Returns 1 on success, 0 with the
 * reason in net_error_text when IPX is absent or the socket cannot be
 * opened. */
int NetIpxStart(void)
{
    RmBlock *blk;
    NetIpxState __far *st;
    unsigned short sock;
    char __far *ep;
    short i;

    if (net_ipx_buf == 0) {
        net_ipx_buf = NetAllocReal(0x842);
        st = (NetIpxState __far *)((RmBlock *)net_ipx_buf)->base;
        st->socket = 0;
    } else {
        NetResizeReal(net_ipx_buf, 0x842);
    }
    blk = (RmBlock *)net_ipx_buf;
    st = (NetIpxState __far *)blk->base;
    st->packet_id = 0xffffffffUL;
    if (IpxInstalled() == 0) {
        memcpy(net_error_text, ipx_error, sizeof(ipx_error));
        RealModeFree(net_ipx_buf);
        net_ipx_buf = 0;
        return 0;
    }
    sock = IpxOpenSocket(0x40);
    st = (NetIpxState __far *)blk->base;
    st->socket = sock;
    if (sock == 0) {
        RealModeFree(net_ipx_buf);
        net_ipx_buf = 0;
        return 0;
    }
    IpxSetup(blk->seg, (unsigned short)((unsigned long)blk->base + 2));
    _fmemset(st->ecb, 0, NET_ECB_COUNT * NET_ECB_SIZE);

    /* ECBs 1..9 are the receive ring; each carries the socket and points its
     * one fragment at its own packet area (slot+0x2a). */
    ep = (char __far *)st->ecb;
    for (i = 1; i < NET_ECB_COUNT; i++) {
        NetEcb __far *ecb = &st->ecb[i];

        ecb->esr = 0;
        ecb->socket = st->socket;
        ecb->frag_count = 1;
        ecb->frag_off = (unsigned short)((unsigned long)(ep + i * NET_ECB_SIZE + 0x2a) & 0xffff);
        ecb->frag_seg = blk->seg;
        ecb->frag_size = 0xa6;
        IpxListen(blk->seg, (unsigned short)((unsigned long)(ep + i * NET_ECB_SIZE) & 0xffff));
    }

    /* Slot 0 is the transmit ECB: the extra words hold the session stamp the
     * partner checks and the command counter used by the handshake. */
    st->ecb[0].esr = 0;
    st->ecb[0].socket = st->socket;
    st->ecb[0].frag_count = 1;
    st->ecb[0].frag_off = (unsigned short)((unsigned long)ep + 0x2a);
    st->ecb[0].frag_seg = blk->seg;
    st->ecb[0].frag_size = 0xa6;
    ep[0x2f] = 4;
    *(unsigned long *)(ep + 0x30) = st->session;
    *(unsigned short *)(ep + 0x3a) = st->socket;
    return 1;
}
