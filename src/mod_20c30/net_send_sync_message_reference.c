/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * NetSendSyncMessage (0x21cb8, PACKET.C): send the 18-byte save/load sync
 * block as message type 0x11 (3-byte header + 0x12 bytes).
 *
 * Reference C: the compiled code is identical to 0x21cb8 except for two
 * filler bytes the original has before the final `ret` (0x21ce6:
 * `mov eax,eax`, a 2-byte no-op that no C spelling of this function
 * produces); see the symbol entry's t3_blocker. */
#include "mod_20c30.h"

/* 18-byte NetSync block (0x5a0a2); the sender only copies it. */
typedef struct Sync18 {
    unsigned long w[4];
    unsigned short tail;
} Sync18;

/* @0x21cb8 */
void NetSendSyncMessage(void *msg)
{
    char buf[0x84];

    buf[0] = 0x11;
    *(Sync18 *)(buf + 3) = *(Sync18 *)msg;
    PacketSend(0x15, buf);
}
