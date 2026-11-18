/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * EvtInit (0x316a0): zero the ISR-visible state block (0x5a880..0x5aa5e,
 * 0x1df bytes), set the move/idle event templates and the 160,100 start
 * position, allocate the ring (queue_size 12-byte events), copy the 0x80-byte
 * scancode fixup table and DPMI-lock both the data block and the ISR code
 * region [IsrRegionStart, IsrRegionEnd].
 */
#include "input.h"

void *memset(void *dst, int c, unsigned n);          /* 0x30c50 */
void *memcpy(void *dst, const void *src, unsigned n);/* 0x31789 */
void *GdsAlloc(unsigned size);                       /* 0x32558 */
void DpmiLockRegion(void *addr, unsigned size);      /* 0x312f0 */

extern unsigned char scancode_fixup_source[0x80];    /* 0x553b4 */

#define EVT_STATE_SIZE 0x1df

/* @0x316a0 */
void EvtInit(unsigned short queue_size)
{
    memset(&evt_key, 0, EVT_STATE_SIZE);
    evt_move.type = 1;
    evt_move.sub = 3;
    evt_idle.type = 0x400;
    evt_idle.sub = 8;
    mouse_raw_x = 0xa0;
    mouse_raw_y = 0x64;
    evt_mask = 0;
    evt_queue = GdsAlloc((unsigned)queue_size * sizeof(Event));
    evt_queue_size = queue_size;
    memcpy(scancode_fixup_table, scancode_fixup_source, 0x80);
    DpmiLockRegion(&evt_key, EVT_STATE_SIZE);
    DpmiLockRegion((void *)IsrRegionStart,
                   (unsigned)IsrRegionEnd - (unsigned)IsrRegionStart + 1);
}
