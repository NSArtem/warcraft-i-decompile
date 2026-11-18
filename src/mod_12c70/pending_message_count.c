/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetPendingMessageCount (0x12d04), built from C: T3 under Watcom 10.0a.
 * Its own object because the neighbours NetNextSendSlot 0x12cec and
 * NetFindSentRecord 0x12d2c are separate files.
 *
 * The int return type is what the original does: the subtraction is left in
 * eax unmasked (a caller compares it with `cmp eax,7; jge`, a signed test).
 * Names/evidence: analysis/symbols/net_link.toml.
 */
#include "net_link.h"

/* @0x12d04  how many sent records are still outstanding; the link mode word
 * gates the whole computation, so a non-linked game reports zero. */
int NetPendingMessageCount(void)
{
    int done;
    int seq;

    if (dat_516ae != 0) {
        done = net_send_state[2];
        seq = net_send_state[0];
        return seq - done;
    }
    return 0;
}
