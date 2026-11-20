/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_34860_c.h"

extern unsigned char palette_cycles[];

/* @0x34860 */
void __cdecl PaletteCycleSetup(unsigned char id, unsigned char period, unsigned char first, unsigned char last, void *list, unsigned char count)
{
    palette_cycles[id * 12 + 2] = period;
    palette_cycles[id * 12 + 3] = period;
    palette_cycles[id * 12 + 4] = first;
    palette_cycles[id * 12 + 5] = 0;
    palette_cycles[id * 12 + 6] = last;
    *(void **)(palette_cycles + id * 12 + 7) = list;
    palette_cycles[id * 12 + 11] = count;
}
