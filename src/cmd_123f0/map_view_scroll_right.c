/* codegen-flags: -s -ot -oa -4r -zp2 */
/* codegen-compiler: 10.0a */
/* CMD.C 0x126e4 - see docs/subsystems/cmd_123f0.md and
 * analysis/symbols/cmd_123f0.toml.  One function per object: wcc386 aligns
 * every following function to 16 bytes, so a multi-function file would make
 * wc1.match compare trailing filler against the *next* original function. */
#include "cmd_123f0.h"

/* @0x126e4 */
void MapViewScrollRight(unsigned short n)
{
    map_scroll_x += n;
    if (map_scroll_x > map_scroll_x_max)
        map_scroll_x = map_scroll_x_max;

    while (tile_cache_left != map_scroll_x) {
        TerrainCacheColumn(tile_cache_left + 15);
        tile_cache_left++;
    }
    tile_cache_left = map_scroll_x;
}
