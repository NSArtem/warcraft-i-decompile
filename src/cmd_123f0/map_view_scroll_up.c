/* codegen-flags: -s -ot -oa -4r -zp2 */
/* codegen-compiler: 10.0a */
/* CMD.C 0x125c4 - see docs/subsystems/cmd_123f0.md and
 * analysis/symbols/cmd_123f0.toml.  One function per object: wcc386 aligns
 * every following function to 16 bytes, so a multi-function file would make
 * wc1.match compare trailing filler against the *next* original function. */
#include "cmd_123f0.h"

/* @0x125c4 */
void MapViewScrollUp(unsigned short n)
{
    map_scroll_y -= n;
    if ((short)map_scroll_y < 0)
        map_scroll_y = 0;

    while (tile_cache_top != map_scroll_y) {
        tile_cache_top--;
        TerrainCacheRow(tile_cache_top);
    }
    tile_cache_top = map_scroll_y;
}
