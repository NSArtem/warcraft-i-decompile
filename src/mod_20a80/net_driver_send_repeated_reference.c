/* codegen-compiler: 10.0a */
#include "mod_20a80.h"

extern unsigned short net_sync_counter;

/* @0x20bd4 */
void NetDriverSendRepeated(void *buf_off, unsigned buf_seg, unsigned short len)
{
    short i;

    ((void (*)(void *, unsigned, unsigned))net_driver_send)(buf_off, buf_seg, len);
    for (i = 0; i < net_sync_counter; i++) {
        ((void (*)(void *, unsigned, unsigned))net_driver_send)(buf_off, buf_seg, len);
    }
}
