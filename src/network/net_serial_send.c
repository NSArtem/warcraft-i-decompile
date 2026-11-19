/* codegen-compiler: 10.0a */
/* 0x1fd30 NetSerialSend: encode one frame (0x70 doubling, 0x70 0x00
 * terminator) into net_tx_frame and queue it. */
#include "network.h"

void NetSerialSend(void __far *msg, unsigned len)
{
    NetUart *u;
    unsigned char far *p = (unsigned char far *)msg;
    unsigned char *out = (unsigned char *)net_tx_frame;
    unsigned short i = 0;
    unsigned short n = (unsigned short)len;
    unsigned char ch;

    if (n > NET_FRAME_MAX) {
        u = (NetUart *)net_uart;
        u->tx_too_long++;
        if (n > u->tx_longest)
            u->tx_longest = u->tx_longest + 1;
        return;
    }
    u = (NetUart *)net_uart;
    if (n > u->tx_max)
        u->tx_max = n;
    if (n < u->tx_min)
        u->tx_min = n;
    u->tx_total += n;
    u->tx_frames++;
    while (n-- != 0) {
        ch = *p;
        if (ch == 0x70)
            out[i++] = 0x70;
        out[i++] = ch;
        p++;
    }
    out[i++] = 0x70;
    out[i++] = 0;
    NetSerialQueueBytes(out, i);
}
