/* codegen-compiler: 10.0a */
#include "mod_209e0.h"

extern short NetDriverReceiveChecked(void __far *buf);

/* @0x20a14 */
int NetReceivePacketChecked(unsigned char *pkt)
{
    short r = NetDriverReceiveChecked(pkt);

    if (r != 0) {
        if (r != -1) {
            if (NetChecksum(pkt + 4, pkt[4]) == *(unsigned short *)pkt)
                return 1;
        }
        pkt[5] = 1;
        return -1;
    }
    return r;
}
