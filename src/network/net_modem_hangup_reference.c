/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x2094c NetModemHangup (docs/subsystems/network.md): drop
 * DTR, send the escape and hang-up commands and drain the receiver.
 * Verified differentially by tests/test_network.py (T4). */
#include <conio.h>
#include <dos.h>
#include "network.h"

void NetModemHangup(void)
{
    NetUart *u = (NetUart *)net_uart;

    outp(u->io_base + 4, inp(u->io_base + 4) & 0xfe);
    delay(0x4e2);
    u = (NetUart *)net_uart;
    outp(u->io_base + 4, inp(u->io_base + 4) | 1);
    NetModemCommand(net_cmd_escape);
    delay(0x4e2);
    NetModemCommand(modem_hangup);
    delay(0xc8);
    while ((short)NetSerialGetByte() != -1)
        ;
}
