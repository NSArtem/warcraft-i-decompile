/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * PacketCheckSync (0x21554): compare the sync ids of the two command packets
 * executed this tick; a mismatch means the two simulations diverged.  The
 * report is latched through packet_sync_error so the message appears once.
 * Only caller: PacketTick 0x21956.
 * The two ids are compared as direct memory expressions (a pair of locals
 * gives a different register allocation). */
#include "packet.h"

/* @0x21554 */
void PacketCheckSync(unsigned char *local, unsigned char *remote)
{
    if (net_play_flag == 0 || packet_sync_error != 0)
        return;
    if (local[0] == 0 || remote[0] == 0)
        return;
    if (*(unsigned short *)(local + 1) != 0 &&
        *(unsigned short *)(remote + 1) != 0 &&
        *(unsigned short *)(local + 1) != *(unsigned short *)(remote + 1)) {
        packet_sync_error = 1;
        FatalError("A syncing error occurred during gameplay");
    }
}
