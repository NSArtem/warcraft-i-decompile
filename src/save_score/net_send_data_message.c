/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendDataMessage (0x24780), built from C: T3 under Watcom 10.0a.  It was
 * reference C under OW2; split out of src/save_score/save_reference.c, whose
 * declarations it repeats.
 */
#include "save_score.h"

extern unsigned char net_msg[0x10];                /* 0x5a000 */
extern unsigned short net_sync_state[2];           /* 0x5310c: [0] = link up */
extern void *memcpy(void *dst, const void *src, unsigned n);

/* 0x131d8: stamps the sequence word and hands net_msg to the link's send ring. */
extern void NetSendMessage(unsigned char *msg);

/* @0x24780  hand `len` bytes to the partner as a type-4 message (or the
 * empty type-1 message for len == 0); nothing is sent without a link. */
void NetSendDataMessage(unsigned short len, void *data)
{
    if (len != 0) {
        net_msg[0] = (unsigned char)(len + 4);
        net_msg[1] = 4;
        memcpy(net_msg + 4, data, len);
    } else {
        net_msg[0] = 4;
        net_msg[1] = 1;
    }
    if (net_sync_state[0] != 0)
        NetSendMessage(net_msg);
}
