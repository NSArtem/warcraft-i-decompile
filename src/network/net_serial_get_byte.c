/* codegen-compiler: 10.0a */
/* 0x201c0 NetSerialGetByte: pop one byte of the receive ring; -1 when the
 * interrupt handler has queued none. */
#include "network.h"

int NetSerialGetByte(void)
{
    NetUart *u = (NetUart *)net_uart;
    short i;
    unsigned char c;

    if (u->rx_count == 0)
        return -1;
    i = u->rx_tail++;
    c = u->rx_buf[i];
    u->rx_count--;
    u->rx_bytes++;
    if (u->rx_tail >= NET_RING)
        u->rx_tail = 0;
    return c;
}
