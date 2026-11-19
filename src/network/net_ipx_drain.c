/* codegen-compiler: 10.0a */
/* 0x1f564 NetIpxDrain: discard every pending IPX packet. */
#include "network.h"

void NetIpxDrain(void)
{
    while (NetIpxReceive((char __far *)((RmBlock *)net_ipx_buf)->base + 0x72) != 0)
        ;
}
