/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x200e8 NetSerialUartStop (docs/subsystems/network.md):
 * turn the UART interrupts off, mask the IRQ and restore both interrupt
 * vectors.  Verified differentially by tests/test_network.py (T4). */
#include <i86.h>
#include "network.h"

void NetSerialUartStop(void)
{
    NetUart *u = (NetUart *)net_uart;
    union REGS r;

    outp(u->io_base + 1, 0);
    outp(u->io_base + 4, 0);
    outp(u->io_base + 2, 0);
    outp(0x21, inp(0x21) | (1 << u->irq));
    r.w.ax = 0x201;
    r.h.bl = (unsigned char)net_irq_vector;
    r.w.cx = net_old_vector_seg;
    r.w.dx = net_old_vector_off;
    int386(0x31, &r, &r);
    r.w.ax = 0x205;
    r.h.bl = (unsigned char)net_irq_vector;
    r.w.cx = net_old_isr_sel;
    r.x.edx = net_old_isr_off;
    int386(0x31, &r, &r);
}
