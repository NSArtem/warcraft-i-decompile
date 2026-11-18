/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetFindReceivedRecord (0x12d7c), built from C: T3 under Watcom 10.0a.
 * One function per object: the neighbours are separate files, and a file
 * with several functions gets 16-byte aligned by wcc386 (the original module
 * is not).  Names/evidence: analysis/symbols/net_link.toml.
 */
#include "net_link.h"

/* @0x12d7c  find a received record with this sequence number, skipping the
 * link acks (type 3): they never satisfy an awaited reply. */
struct NetRingRecord *NetFindReceivedRecord(unsigned short seq)
{
    short i;

    for (i = 0; i < NET_RECV_SLOTS; i++)
        if (((struct NetRingRecord *)net_recv_ring)[i].seq == seq &&
            (((struct NetRingRecord *)net_recv_ring)[i].type & 0x3f) != 3)
            return (struct NetRingRecord *)net_recv_ring + i;
    return 0;
}
