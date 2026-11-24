/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x1f854 NetSerialStart (docs/subsystems/network.md).
 * Verified differentially by tests/test_network.py (T4). */
#include <string.h>
#include "network.h"
#include "dos_realmode_mem_f1.h"

int  DpmiLockRegion(void *addr, unsigned size);      /* 0x312f0 (input.toml) */
unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
                                                    /* 0x31844 */
void *ResourceRead(void *dest, unsigned count);     /* 0x32740 */

/* 0x1f854: bring the serial/modem transport up: allocate and lock the UART
 * state, fill the link settings, load the real-mode interrupt stub and
 * program the UART. */
int NetSerialStart(void)
{
    NetUart *u;
    RmBlock *blk;
    unsigned short stub_len;

    if (net_uart_buf == 0) {
        net_uart_buf = RealModeAlloc(0x1076);
        blk = (RmBlock *)net_uart_buf;
        net_uart = (void *)((unsigned long)blk->seg << 4);
        DpmiLockRegion(&net_uart, 4);
        DpmiLockRegion((void *)&NetSerialIsrAnchor, 1);
    }
    u = (NetUart *)net_uart;
    u->io_base = 0xffff;
    if (net_modem_link != 0) {
        u->irq = modem_irq;
        u->port = modem_port;
        u->baud = modem_baud;
    } else {
        u->irq = serial_irq;
        u->port = serial_port;
        u->baud = serial_baud;
    }
    u->modem_status = 0xffff;
    u->line_status = 0xffff;
    u->rx_head = 0;
    u->rx_tail = 0;
    u->rx_count = 0;
    u->tx_head = 0;
    u->tx_tail = 0;
    u->tx_count = 0;
    u->cts_count = 0;
    u->dcd_count = 0;
    u->ri_count = 0;
    u->dsr_count = 0;
    u->tx_ints = 0;
    u->rx_ints = 0;
    u->tx_overflow = 0;
    u->rx_bytes = 0;
    u->rx_frames = 0;
    u->rx_max = 0;
    u->rx_min = 0xffffffffUL;
    u->rx_overrun = 0;
    u->rx_total = 0;
    u->rx_too_long = 0;
    u->rx_longest = 0;
    u->rx_long_run = 0;
    u->word105a = 0;
    u->tx_frames = 0;
    u->tx_max = 0;
    u->tx_min = 0xffffffffUL;
    u->tx_total = 0;
    u->tx_too_long = 0;
    u->tx_longest = 0;

    if (net_irq_buf == 0) {
        stub_len = (unsigned short)ResourceBegin(0xd9, 0);
        net_irq_buf = RealModeAlloc(stub_len);
    }
    blk = (RmBlock *)net_irq_buf;
    net_vector_table = (unsigned long)blk->seg << 4;
    ResourceBegin(0xd9, 0);
    ResourceRead((void *)net_vector_table, 0);
    *(unsigned short *)((char *)net_vector_table + 4) =
        ((RmBlock *)net_uart_buf)->seg;

    NetSerialFixPort();
    NetSerialUartInit();

    u = (NetUart *)net_uart;
    if (net_link_speed_set == 0xffff) {
        if (net_modem_link != 0 || u->baud <= 0x2580) {
            net_link_speed = 3;
            if (u->baud == 0x960)
                net_link_speed = 4;
        } else {
            net_link_speed = 0;
        }
    }
    if (net_port_base[0] == 0xffff && net_uart_fifo == 0) {
        u = (NetUart *)net_uart;
        if (u->baud != 0x960)
            net_sync_counter = 1;
    }
    return 1;
}
