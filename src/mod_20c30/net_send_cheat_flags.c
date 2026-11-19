/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * NetSendCheatFlags (0x21c44, PACKET.C): forward the player's cheat word to
 * the other machine as message type 0x10 (3-byte header + the dword). */
#include "mod_20c30.h"

/* @0x21c44 */
void NetSendCheatFlags(unsigned long flags)
{
    char msg[0x84];

    msg[0] = 0x10;
    *(unsigned long *)(msg + 3) = flags;
    fn_214d4(7, msg);
}
