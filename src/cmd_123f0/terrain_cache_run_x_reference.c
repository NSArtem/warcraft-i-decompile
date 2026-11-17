/* codegen-flags: -s -ot -oa -4r -zp2 */
/* CMD.C 0x124e8 - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * REFERENCE C (not built, no `src =` entry): the original spills the constant `y`
 * argument and reloads it with a 16-bit zero-extension every iteration, and promotes the
 * counter for the compare
 * (`xor eax,eax; mov ax,si; cmp eax,0xf; jl`); OW2 keeps y in a register and narrows
 * the compare - V1/V3/V4/V10.
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"
/* @0x124e8 */
void TerrainCacheRunX(unsigned short *row, unsigned short x, unsigned short y)
{
    unsigned short i;

    for (i = 0; i < 15; i++)
        TerrainTileToCache(*row++, x++, y);
}
