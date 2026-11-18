/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetResetLink (0x12c70), built from C: T3 under Watcom 10.0a.
 * One function per object: the neighbours are separate files, and a file
 * with several functions gets 16-byte aligned by wcc386 (the original module
 * is not).  Names/evidence: analysis/symbols/net_link.toml.
 */
#include "net_link.h"

/* 0x21974 (PACKET.C): clears the outgoing packet id before a session. */
extern void NetResetPacketId(void);
extern void *memset(void *dst, int c, unsigned n);

/* @0x12c70  rewind the whole link state: sequences back to 1, the receive
 * slot to 0, the send slot to 9 (the ring is used backwards), both rings and
 * the packet id cleared. */
void NetResetLink(void)
{
    unsigned short one = 1;
    unsigned short zero = 0;

    net_send_state[2] = one;
    net_send_state[1] = one;
    net_send_state[0] = one;
    net_ring_state[0] = zero;
    net_send_slot = 9;
    net_reply_pending = zero;
    NetResetPacketId();
    memset(net_send_ring, 0, NET_SEND_SLOTS * sizeof(struct NetRingRecord));
    memset(net_recv_ring, 0, NET_RECV_SLOTS * sizeof(struct NetRingRecord));
}
