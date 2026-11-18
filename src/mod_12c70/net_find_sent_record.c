/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetFindSentRecord (0x12d2c), built from C: T3 under Watcom 10.0a.
 * The index is a `short` and the ring is cast per access: that spelling is
 * what reproduces the original`s `movsx`/`imul` loop (a struct pointer local
 * gets strength-reduced to a pointer walk by wcc386).
 * One function per object: the neighbours are separate files, and a file
 * with several functions gets 16-byte aligned by wcc386 (the original module
 * is not).  Names/evidence: analysis/symbols/net_link.toml.
 */
#include "net_link.h"

/* @0x12d2c  find the sent record with this sequence number; the current and
 * the next sequence are still in flight, so they are rejected up front. */
struct NetRingRecord *NetFindSentRecord(unsigned short seq)
{
    short i;

    if (seq == net_send_state[0] || seq == net_send_state[0] + 1)
        return 0;
    for (i = 0; i < NET_SEND_SLOTS; i++)
        if (((struct NetRingRecord *)net_send_ring)[i].seq == seq)
            return (struct NetRingRecord *)net_send_ring + i;
    return 0;
}
