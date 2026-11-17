/* codegen-flags: -s -ot -oa -4r -zp2 */
/* CMD.C 0x12524 - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * REFERENCE C (not built, no `src =` entry): same shape as TerrainCacheRunX, 11 iterations
 * (`cmp eax,0xb`).
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"
/* @0x12524 */
void TerrainCacheRunY(unsigned short *col, unsigned short x, unsigned short y)
{
    unsigned short i;

    for (i = 0; i < 11; i++) {
        TerrainTileToCache(*col, x, y++);
        col += 64;
    }
}
