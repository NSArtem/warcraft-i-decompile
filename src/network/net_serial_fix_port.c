/* codegen-compiler: 10.0a */
/* 0x1fe04 NetSerialFixPort: resolve the UART's io base and IRQ from the COM
 * port number when they are 0xffff (net_port_base 0x52a62, net_port_irq
 * 0x52a6c).  The original reads the packed io-base/IRQ and IRQ/port dwords
 * (codegen.md dword-view idiom) and re-loads net_uart for the second test. */
#include "network.h"

void NetSerialFixPort(void)
{
    NetUart *u = (NetUart *)net_uart;

    if ((*(int *)&u->io_base >> 16) == -1)
        u->irq = net_port_irq[(*(int *)&u->irq >> 16) - 1];
    u = (NetUart *)net_uart;
    if ((*(short *)&u->io_base) == -1)
        u->io_base = net_port_base[*(int *)&u->irq >> 16];
}
