/* codegen-compiler: 10.0a */
/* 0x1fbc8 NetSerialReceive: reassemble one 0x70-escaped frame from the byte
 * queue and return its length (0 while no frame is complete). */
#include <i86.h>
#include "network.h"

int NetSerialReceive(void __far *msg)
{
    NetUart *u = (NetUart *)net_uart;
    int c;

    if (u->rx_count > 0x7fc) {
        u->rx_overrun++;
        _disable();
        u->rx_tail = u->rx_head;
        u->rx_count = 0;
        _enable();
        net_rx_frame_done = 1;
        return 0;
    }
    if (net_rx_frame_done != 0) {
        net_rx_length = 0;
        net_rx_frame_done = 0;
        u->rx_long_run = 0;
    }
    for (;;) {
        c = NetSerialGetByte();
        if ((short)c < 0)
            return 0;
        if (net_rx_escape != 0) {
            net_rx_escape = 0;
            if (c != 0x70) {
                /* the byte after the escape is not a 0x70: frame complete */
                net_rx_frame_done = 1;
                u = (NetUart *)net_uart;
                u->rx_frames++;
                if (net_rx_length > u->rx_max)
                    u->rx_max = net_rx_length;
                if (net_rx_length < u->rx_min)
                    u->rx_min = net_rx_length;
                u->rx_total += net_rx_length;
                return net_rx_length;
            }
        } else if (c == 0x70) {
            net_rx_escape = 1;
            continue;
        }
        u = (NetUart *)net_uart;
        if (net_rx_length >= NET_FRAME_MAX) {
            u->rx_long_run++;
            u->rx_too_long++;
            if (u->rx_long_run > u->rx_longest)
                u->rx_longest = u->rx_long_run;
        } else {
            ((unsigned char __far *)msg)[net_rx_length] = (unsigned char)c;
            net_rx_length++;
        }
    }
}
