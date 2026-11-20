/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for the two serial interrupt handlers 0x202c0 NetSerialIsr and
 * 0x20448 NetSerialIsrFifo (docs/subsystems/network.md).  They share the
 * EOI/exit block at 0x20494 in the original (NetSerialIsr jumps into it), so
 * they must be reconstructed together - this is one object with both
 * functions in image order.  Verified differentially by tests/test_network.py
 * with the COM ports modelled (T4). */
#include <i86.h>
#include "network.h"

/* The 8259's end-of-interrupt and the interrupt frame's exit; the original
 * emits this tail once, at the end of NetSerialIsrFifo. */
#define NET_EOI() outp(0x20, 0x20)

void __interrupt NetSerialIsr(void)
{
    NetUart *u;
    unsigned char iir;
    unsigned char c;
    short i;

    for (;;) {
        u = (NetUart *)net_uart;
        iir = inp(u->io_base + 2) & 7;
        if (iir == 4) {
            u->rx_ints++;
            c = inp(u->io_base);
            i = u->rx_head++;
            u->rx_buf[i] = c;
            u->rx_count++;
            if (u->rx_head >= NET_RING)
                u->rx_head = 0;
        } else if (iir == 2) {
            u->tx_ints++;
            if (u->tx_count != 0) {
                i = u->tx_tail++;
                c = u->tx_buf[i];
                u->tx_count--;
                if (u->tx_tail >= NET_RING)
                    u->tx_tail = 0;
                outp(u->io_base, c);
            }
        } else if (iir == 6) {
            u->line_status = inp(u->io_base + 5);
            if (u->line_status & 0x02)
                u->dsr_count++;
            if (u->line_status & 0x04)
                u->ri_count++;
            if (u->line_status & 0x08)
                u->dcd_count++;
            if (u->line_status & 0x10)
                u->cts_count++;
        } else {
            NET_EOI();
            return;
        }
    }
}

void __interrupt NetSerialIsrFifo(void)
{
    NetUart *u;
    unsigned char iir;
    unsigned char c;
    short i;
    short n;

    for (;;) {
        u = (NetUart *)net_uart;
        iir = inp(u->io_base + 2) & 7;
        if (iir == 4) {
            do {
                u = (NetUart *)net_uart;
                c = inp(u->io_base);
                i = u->rx_head++;
                u->rx_buf[i] = c;
                u->rx_count++;
                if (u->rx_head >= NET_RING)
                    u->rx_head = 0;
            } while ((inp(u->io_base + 5) & 1) != 0);
        } else if (iir == 2) {
            for (n = 0x10; n != 0; n--) {
                u = (NetUart *)net_uart;
                if (u->tx_count == 0)
                    break;
                i = u->tx_tail++;
                c = u->tx_buf[i];
                u->tx_count--;
                if (u->tx_tail >= NET_RING)
                    u->tx_tail = 0;
                outp(u->io_base, c);
            }
        } else if (iir == 6) {
            u->line_status = inp(u->io_base + 5);
            if (u->line_status & 0x02)
                u->dsr_count++;
            if (u->line_status & 0x04)
                u->ri_count++;
            if (u->line_status & 0x08)
                u->dcd_count++;
            if (u->line_status & 0x10)
                u->cts_count++;
        } else {
            NET_EOI();
            return;
        }
    }
}
