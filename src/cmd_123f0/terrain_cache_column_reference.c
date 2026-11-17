/* codegen-flags: -s -ot -oa -4r -zp2 */
/* CMD.C 0x12594 - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * REFERENCE C (not built, no `src =` entry): mirror of TerrainCacheRow for a column; the
 * same V1/V3 differences.
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"
/* @0x12594 */
void TerrainCacheColumn(unsigned short x)
{
    unsigned short y = map_scroll_y;
    unsigned short *col = tile_map + ((unsigned long)y << 6);

    TerrainCacheRunY(col + x, x, y);
}
