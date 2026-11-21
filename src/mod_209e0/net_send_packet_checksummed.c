/* codegen-compiler: 10.0a */
#include "mod_209e0.h"

extern void NetDriverSendRepeated(void __far *buf, unsigned short len);

/* @0x20a50 */
void NetSendPacketChecksummed(unsigned char *pkt, unsigned short word)
{
    *(unsigned short *)pkt = NetChecksum(pkt + 4, pkt[4]);
    *(unsigned short *)(pkt + 2) = word;
    NetDriverSendRepeated(pkt, word);
}
