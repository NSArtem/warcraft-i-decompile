/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* CMD.C 0x1274c - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * Built from C: T3 under Watcom 10.0a (codegen-compiler).  Under OW2 it was reference C: the two clamps compile identically; the
 * rebuild loop again promotes the counter for
 * the compare and keeps the row pointer in the other register - V1/V3/V10.
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"
/* @0x1274c */
void MapViewSetScroll(short x, short y)
{
    unsigned short *p;
    unsigned short i;

    if (x < 0)
        x = 0;
    else if (x > map_scroll_x_max)
        x = map_scroll_x_max;
    map_scroll_x = x;
    tile_cache_left = x;

    if (y < 0)
        y = 0;
    else if (y > map_scroll_y_max)
        y = map_scroll_y_max;
    map_scroll_y = y;
    tile_cache_top = y;

    p = tile_map + ((unsigned long)map_scroll_y << 6) + map_scroll_x;
    for (i = 0; i < 11; i++) {
        TerrainCacheRunX(p, map_scroll_x, map_scroll_y + i);
        p += 64;
    }
}
