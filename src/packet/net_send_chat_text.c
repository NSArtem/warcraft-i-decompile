/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendChatText (0x21c68, named in mod_20c30.toml): send typed chat text to
 * the partner (type 0xf) and show "message sent to opponent".  Two-player
 * only.  Receiver: PacketDispatch row 0xf -> fn_19edc (the in-game message
 * window) when the packet belongs to the partner slot. */
#include "packet.h"

extern void fn_19f70(const char *msg, unsigned code);   /* 0x19f70 */

/* @0x21c68 */
void NetSendChatText(const char *text, unsigned short len)
{
    unsigned char msg[PKT_BUF];

    if (net_play_flag == 0)
        return;
    if (len == 0)
        return;
    msg[0] = PKT_CHAT;
    strcpy((char *)(msg + 3), text);
    PacketSend((unsigned short)(len + 4), msg);
    fn_19f70("message sent to opponent", 0x24);
}
