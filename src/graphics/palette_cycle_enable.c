/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_31920 (0x31920..0x31940), DBG style, cdecl. */
#include "graphics.h"

/* @0x31920 */
void __cdecl PaletteCycleEnable(unsigned char id)
{
    *(unsigned short *)(palette_cycles + id * 12) = 1;
}
