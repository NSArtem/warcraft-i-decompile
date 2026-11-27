/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * PacketGenerateId (0x214b0): fold the shared LCG state into the outgoing
 * packet id.  Both machines advance dat_50d7c identically, so the word is a
 * synchronization checksum: PacketSend stamps it into the next packet and
 * PacketCheckSync compares the two directions' stamps once per tick.
 * Only caller: PacketTick (when two-player, the game screen is up and no
 * message is outstanding). */
#include "packet.h"

/* @0x214b0 */
void PacketGenerateId(void)
{
    unsigned short id;
    long h;

    h = (dat_50d7c >> 16) ^ dat_50d7c;
    id = (unsigned short)h;
    if (id == 0)
        id = 1;
    packet_id = id;
}
