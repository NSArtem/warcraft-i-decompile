/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 */
#include "mod_33220_c.h"
#include <string.h>

extern char palette_cycles[16][12];

/* @0x334fc */
void PaletteCyclesClear(void)
{
    memset(palette_cycles, 0, 0xc0);
}
