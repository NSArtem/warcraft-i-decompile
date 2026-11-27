/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern short NetLinkHandshake(void);   /* 0x23edc, SAVE.C */

/* @0x15230: the callback NetGameStart hands to the network-progress dialog;
 * it runs the handshake and reports success through 0x516ae. */
int NetGameHandshakeCallback(void)
{
    dat_516ae = NetLinkHandshake();
    return 1;
}
