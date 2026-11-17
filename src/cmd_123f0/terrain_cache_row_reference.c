/* codegen-flags: -s -ot -oa -4r -zp2 */
/* CMD.C 0x12564 - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * REFERENCE C (not built, no `src =` entry): the original scales the row with `shl eax,7`
 * *before* loading map_scroll_x and uses
 * `lea eax,[edx*2]`; OW2 loads the scroll first and emits `lea eax,[edx+edx]` plus an
 * extra `and edx,0xffff` - V1/V3.
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"
/* @0x12564 */
void TerrainCacheRow(unsigned short y)
{
    unsigned short *row = tile_map + ((unsigned long)y << 6);

    TerrainCacheRunX(row + map_scroll_x, map_scroll_x, y);
}
