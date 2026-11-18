/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetNextRecvSlot (0x12cd4), built from C: T3 under Watcom 10.0a.
 * One function per object: the neighbours are separate files, and a file
 * with several functions gets 16-byte aligned by wcc386 (the original module
 * is not).  Names/evidence: analysis/symbols/net_link.toml.
 */
#include "net_link.h"

/* @0x12cd4  advance a 0..3 ring index; the promoted int compare is the
 * original's `cmp edx,4` (docs/subsystems/codegen.md V4). */
unsigned short NetNextRecvSlot(unsigned short *counter)
{
    int v;

    (*counter)++;
    v = *counter;
    if (v >= NET_RECV_SLOTS)
        *counter = 0;
    return *counter;
}
