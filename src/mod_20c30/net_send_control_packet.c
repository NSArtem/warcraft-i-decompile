/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * NetSendControlPacket (0x21c20, PACKET.C): a 5-byte control message, type
 * 0xe, with the 16-bit id at +3.  status.toml already names 0x21c20 (for
 * OpenGameMenu's callee), so the C is reported without a symbol entry. */
#include "mod_20c30.h"

/* @0x21c20 */
void NetSendControlPacket(unsigned short id)
{
    char msg[0x84];

    msg[0] = 0xe;
    *(unsigned short *)(msg + 3) = id;
    PacketSend(5, msg);
}
