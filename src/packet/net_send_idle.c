/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * PacketSendIdle (0x2150c): when nothing is outstanding, send the idle
 * packet - the 3-byte type-1 packet that carries the sync id PacketGenerateId
 * just produced (two-player), or the empty "nothing" link message otherwise.
 * Only caller: PacketTick 0x218d5. */
#include "packet.h"

/* @0x2150c */
void PacketSendIdle(void)
{
    unsigned char msg[PKT_BUF];
    unsigned short len;

    if (NetPendingMessageCount() != 0)
        return;
    if (net_play_flag != 0 && dialog_enabled != 0) {
        msg[0] = PKT_IDLE;
        len = 3;
    } else {
        len = 0;
    }
    PacketSend(len, msg);
}
