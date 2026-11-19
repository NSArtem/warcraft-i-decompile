/* codegen-compiler: 10.0a */
/* 0x20258 NetSerialPushBytes: append len bytes to the transmit ring, byte by
 * byte when the block would wrap past the end of the 0x800-byte ring. */
#include <string.h>
#include "network.h"

void NetSerialPushBytes(const unsigned char *src, unsigned len)
{
    NetUart *u = (NetUart *)net_uart;
    short n = len;

    if (u->tx_head + n >= NET_RING) {
        while (n-- != 0)
            NetSerialPutByte(*src++);
    } else {
        _fmemcpy(u->tx_buf + u->tx_head, src, len);
        u->tx_head += n;
        u->tx_count += n;
    }
}
