/* codegen-flags: -s -ot -oa -4r -zp2 */
/* CMD.C 0x12404 - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * REFERENCE C (not built, no `src =` entry): the original pre-tests the loop with a
 * duplicated exit epilogue and compares a
 * *promoted* `unsigned short` counter (`xor ebx,ebx; mov bx,dx; cmp ebx,0x1000; jl`)
 * where OW2 narrows it to `cmp dx,0x1000; jb` - codegen.md V4/V5/V10 cite this very
 * function.
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"
/* @0x12404 - no reference to it anywhere in v1.22h */
void FogMapClear(void)
{
    unsigned short *p = fog_map;
    unsigned short i;

    for (i = 0; i < 0x1000; i++)
        *p++ = 0;
}
