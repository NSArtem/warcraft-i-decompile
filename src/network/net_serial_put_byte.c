/* codegen-compiler: 10.0a */
/* 0x2020c NetSerialPutByte: append one byte to the transmit ring. */
#include "network.h"

void NetSerialPutByte(unsigned char c)
{
    NetUart *u = (NetUart *)net_uart;
    short i;

    i = u->tx_head++;
    u->tx_buf[i] = c;
    u->tx_count++;
    if (u->tx_head >= NET_RING)
        u->tx_head = 0;
}
