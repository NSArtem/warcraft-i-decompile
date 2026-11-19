/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x1fb0c NetSerialStop (docs/subsystems/network.md). */
#include "network.h"

void NetSerialStop(void)
{
    if (net_modem_link != 0) {
        NetModemHangup();
        net_modem_link = 0;
    }
    NetSerialUartStop();
    if (net_link_speed_set == 0xffff)
        net_link_speed = 0;
    if (net_port_base[0] == 0xffff)
        net_sync_counter = 0;
}
