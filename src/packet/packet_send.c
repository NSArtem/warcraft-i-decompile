/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * PacketSend (0x214d4): the module's send entry.  Paces the command stream -
 * at most
 * seven outstanding link messages - stamps the sync id PacketGenerateId
 * produced into the packet header for every packet of length >= 3, and clears
 * it, so exactly one packet carries each id.  Then hands the payload to
 * NetSendDataMessage, which wraps it in a link type-4 message.
 * The `3u` is what makes the original's unsigned `cmp eax,3; jb` (a plain
 * `len >= 3` promotes the unsigned short to int and compares signed). */
#include "packet.h"

/* @0x214d4 */
void PacketSend(unsigned short len, unsigned char *msg)
{
    if (NetPendingMessageCount() >= 7)
        return;
    if (len >= 3u) {
        *(unsigned short *)(msg + 1) = packet_id;
        packet_id = 0;
    }
    NetSendDataMessage(len, msg);
}
