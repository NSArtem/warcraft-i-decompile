/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x1fe48 NetSerialUartInit (docs/subsystems/network.md): the
 * 16550 setup, the FIFO probe, the DPMI vector save/install and the 8259
 * unmask.  Verified differentially by tests/test_network.py with the DPMI
 * int 31h calls and the COM ports modelled (T4). */
#include <i86.h>
#include "network.h"

void NetSerialUartInit(void)
{
    NetUart *u = (NetUart *)net_uart;
    union REGS r;
    void __interrupt (*handler)(void);
    unsigned long div;
    unsigned short ifr;

    div = u->baud;
    if (div == 0x3840)
        div = 0x4b00;
    div = 0x1c2000UL / (div << 4);
    outp(u->io_base + 3, 0x80);          /* LCR: DLAB */
    outp(u->io_base + 1, 0);             /* divisor high */
    outp(u->io_base, (unsigned char)div);/* divisor low  */
    outp(u->io_base + 3, 0x03);          /* LCR: 8N1 */
    outp(u->io_base + 2, 0x41);          /* FCR: enable + clear rx */
    ifr = (unsigned char)inp(u->io_base + 2);
    if ((ifr & 0xf8) == 0xc0) {
        net_uart_fifo = 1;
    } else {
        net_uart_fifo = 0;
        outp(u->io_base + 2, 0);
    }
    outp(u->io_base + 1, 0);
    outp(u->io_base + 4, (unsigned char)((inp(u->io_base + 4) & 0xe4) | 0x0b));
    inp(u->io_base);
    inp(u->io_base + 2);
    net_irq_vector = (unsigned short)(u->irq + 8);

    if (net_old_isr_off == 0) {
        r.w.ax = 0x204;
        r.h.bl = (unsigned char)net_irq_vector;
        int386(0x31, &r, &r);
        net_old_isr_sel = r.w.cx;
        net_old_isr_off = r.x.edx;
    }
    if (net_old_vector_off == 0) {
        r.x.eax = 0x200;
        r.h.bl = (unsigned char)net_irq_vector;
        int386(0x31, &r, &r);
        net_old_vector_seg = r.w.cx;
        net_old_vector_off = r.w.dx;
    }
    if (net_uart_fifo != 0)
        handler = NetSerialIsrFifo;
    else
        handler = NetSerialIsr;
    r.x.eax = 0x205;
    r.x.ebx = (unsigned long)(short)net_irq_vector;
    r.x.ecx = FP_SEG(handler);
    r.x.edx = (unsigned long)FP_OFF(handler);
    int386(0x31, &r, &r);
    r.x.eax = 0x201;
    r.h.bl = (unsigned char)net_irq_vector;
    r.x.ecx = ((RmBlock *)net_irq_buf)->seg;
    r.x.edx = *(unsigned short *)((char *)net_vector_table + (net_uart_fifo != 0 ? 2 : 0));
    int386(0x31, &r, &r);
    outp(0x21, inp(0x21) & ~(1 << u->irq));
    _disable();
    outp(u->io_base + 1, 7);
    outp(0x20, 0xc2);
    _enable();
}
