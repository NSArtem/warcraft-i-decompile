/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendControlPacket (0x21c20, named in status.toml): send a UI/menu command
 * id (type 0xe) to the partner, which runs it through fn_19c14 - the F10 menu
 * (OpenGameMenu sends 8) and the load-rejected alert (SaveStreamValidate
 * sends 0xc).  Unlike the command-card senders it takes no status-panel lock. */
#include "packet.h"

/* @0x21c20 */
void NetSendControlPacket(unsigned short id)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_CONTROL;
    *(unsigned short *)(msg + 3) = id;
    fn_214d4(5, msg);
}
