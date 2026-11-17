/* codegen-flags: -s -ot -oa -4r -zp2 */
/* CMD.C 0x12438 - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * REFERENCE C (not built, no `src =` entry): same loop shape as FogMapClear (V4/V5/V10).
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"
/* @0x12438 */
void FogMapObscure(void)
{
    unsigned short *p = fog_map;
    unsigned short i;

    for (i = 0; i < 0x1000; i++)
        *p++ |= 0xa0a;
}
