/* codegen-compiler: 10.0a */
#include "mod_12c70_c1.h"

typedef struct NetSendEntry {
    unsigned char b[0x88];
} NetSendEntry;

extern unsigned short net_send_state[3];
extern unsigned short net_send_slot;
extern short dat_516ae;
extern unsigned short own_campaign;
extern NetSendEntry net_send_ring[10];
extern unsigned short NetNextSendSlot(unsigned short *counter);
extern void fn_20a50(void *p, unsigned short n);
extern void *memcpy(void *dst, const void *src, unsigned n);

/* @0x131d8 */
int NetSendMessage(unsigned char *msg)
{
    unsigned short t;
    unsigned long i;

    t = net_send_state[0];
    *(unsigned short *)(msg + 2) = t;
    net_send_state[0] = t + 1;
    NetNextSendSlot(&net_send_slot);
    if (dat_516ae != 0) {
        if (own_campaign != 0) {
            msg[1] |= 0xc0;
        } else {
            msg[1] |= 0x40;
        }
    }
    i = net_send_slot;
    memcpy((unsigned char *)net_send_ring + (((i << 4) + i) << 3) + 4, msg, msg[0]);
    i = net_send_slot;
    fn_20a50((unsigned char *)net_send_ring + (((i << 4) + i) << 3), (unsigned short)(msg[0] + 4));
    return 0;
}
