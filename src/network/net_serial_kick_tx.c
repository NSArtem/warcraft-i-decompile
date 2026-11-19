/* codegen-compiler: 10.0a */
/* 0x2061c NetSerialKickTx: write the next queued byte to the transmit
 * register, unmasking the IRQ first in direct-link mode. */
#include <conio.h>
#include "network.h"

void NetSerialKickTx(void)
{
    NetUart *u = (NetUart *)net_uart;
    unsigned char c;

    if (u->tx_count == 0)
        return;
    if (net_direct_link != 0) {
        inp(u->io_base);
        outp(0x21, inp(0x21) & ~(1 << u->irq));
    }
    c = u->tx_buf[u->tx_tail++];
    u->tx_count--;
    if (u->tx_tail >= NET_RING)
        u->tx_tail = 0;
    outp(u->io_base, c);
}
