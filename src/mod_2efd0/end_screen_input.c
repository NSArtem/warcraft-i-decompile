/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndScreenInput (0x2f90c): event handler of the win/lose screen.  A mouse
 * event (Event.type has none of the 0x380 mouse bits) or a key that produced
 * no ASCII code (ev+0xb == 0) skips the screen by telling the other machine
 * with control packet 0x0b. */
#include "mod_2efd0.h"

/* @0x2f90c */
void EndScreenInput(Event *ev)
{
    if (!(ev->type & 0x380) || ((unsigned char *)ev)[0xb] == 0)
        NetSendControlPacket(0xb);
}
