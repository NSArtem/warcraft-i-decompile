/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x1f230 NetIpxConnect (docs/subsystems/network.md).
 * No T3: the IPX wrappers have no symbol-database entries yet, and the three
 * command values (0xa/0xb/0xc in the state's +0x1a word) are not yet anchored
 * to the partner side of the protocol (open question in the doc).  Verified
 * differentially by tests/test_network.py (T4). */
#include <string.h>
#include <i86.h>
#include <dos.h>
#include "network.h"

static char abort_text[20] = "Connection aborted.";

int NetIpxConnect(void)
{
    RmBlock *blk;
    NetIpxState __far *st;
    char msg[12];
    struct dostime_t t;
    unsigned char last = 0;
    short node = 0;

    blk = (RmBlock *)net_ipx_buf;
    st = (NetIpxState __far *)blk->base;
    /* the two node fields of the transmit ECB (block+0x3e, block+0x56) */
    _fmemset((char __far *)st + 0x3e, 0xff, 6);
    _fmemset((char __far *)st + 0x56, 0xff, 6);
    memcpy(msg, net_signature, 10);
    *(unsigned short *)(msg + 10) = net_node_number;
    st->cmd = 0xa;
    for (;;) {
        blk = (RmBlock *)net_ipx_buf;
        st = (NetIpxState __far *)blk->base;
        if (NetIpxReceive((char __far *)st->ecb[0].data + 0x26) == 0) {
            /* nothing yet: abort key test, then resend the identity once a
             * second has passed */
            if (key_down_table[1] != 0 || key_down_table[1] != key_down_table[46]) {
                memcpy(net_error_text, abort_text, sizeof(abort_text));
                return 0;
            }
            _dos_gettime(&t);
            if (last != t.second) {
                last = t.second;
                NetIpxSend(msg, 12);
            }
            continue;
        }
        st = (NetIpxState __far *)blk->base;
        if (_fmemcmp(msg, (char __far *)st->ecb[0].data + 0x26, 12) != 0)
            continue;
        _fmemcpy((char __far *)st + 0x52, (char __far *)st + 0xe, 10);
        _fmemcpy((char __far *)st + 0x3e, (char __far *)st + 0x12, 6);
        st->cmd = 0xb;
        NetIpxDrain();
        if (st->peer_cmd != 0xb)
            NetIpxSend(msg, 12);
        NetIpxDrain();
        st = (NetIpxState __far *)blk->base;
        st->cmd = 0xc;
        return 1;
    }
}
