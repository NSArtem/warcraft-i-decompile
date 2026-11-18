/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetNextSendSlot (0x12cec), built from C: T3 under Watcom 10.0a.
 * One function per object: the neighbours are separate files, and a file
 * with several functions gets 16-byte aligned by wcc386 (the original module
 * is not).  Names/evidence: analysis/symbols/net_link.toml.
 */
#include "net_link.h"

/* @0x12cec  the same for the ten send slots. */
unsigned short NetNextSendSlot(unsigned short *counter)
{
    int v;

    (*counter)++;
    v = *counter;
    if (v >= NET_SEND_SLOTS)
        *counter = 0;
    return *counter;
}
