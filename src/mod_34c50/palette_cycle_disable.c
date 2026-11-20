/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_34c50_c.h"

extern char palette_cycles[];

/* @0x34c50 */
void __cdecl PaletteCycleDisable(unsigned char id)
{
    *(unsigned short *)(palette_cycles + id * 12) = 0;
}
