/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * NetSendChatText (0x21c68, PACKET.C): send a typed message as type 0xf and
 * print 'message sent to opponent' locally.  Nothing happens outside a link
 * game or for an empty message. */
#include "mod_20c30.h"

char *strcpy(char *dst, const char *src);

/* @0x21c68 */
void NetSendChatText(const char *text, unsigned short len)
{
    char msg[0x84];

    if (net_play_flag == 0)
        return;
    if (len == 0)
        return;
    msg[0] = 0xf;
    strcpy(msg + 3, text);
    len += 4;
    PacketSend(len, msg);
    fn_19f70("message sent to opponent", 0x24);
}
