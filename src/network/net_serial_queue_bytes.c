/* codegen-compiler: 10.0a */
/* 0x1fb60 NetSerialQueueBytes: queue bytes for transmission; when the ring
 * would overflow it is thrown away, and when the transmitter is idle the
 * first byte is written at once (NetSerialKickTx). */
#include <conio.h>
#include "network.h"

void NetSerialQueueBytes(const unsigned char *src, unsigned len)
{
    NetUart *u = (NetUart *)net_uart;

    if (u->tx_count + (short)len > NET_RING) {
        u->tx_overflow++;
        u->tx_count = 0;
        u->tx_tail = u->tx_head;
    }
    NetSerialPushBytes(src, len);
    u = (NetUart *)net_uart;
    if (inp(u->io_base + 5) & 0x40)
        NetSerialKickTx();
}
