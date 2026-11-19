/* codegen-compiler: 10.0a */
/* 0x1fb54 NetSerialDrain: pop every byte the interrupt handler queued; a
 * partially assembled receive frame is dropped with them. */
#include "network.h"

void NetSerialDrain(void)
{
    while ((short)NetSerialGetByte() != -1)
        ;
}
