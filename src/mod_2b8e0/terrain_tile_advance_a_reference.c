/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned short map_scroll_x;
extern unsigned short map_scroll_y;
extern unsigned short *terrain_tbl_a;
extern unsigned short *tile_map;
extern int terrain_scan_y;
extern int terrain_scan_x;
extern unsigned short *terrain_scan_table;
extern unsigned short terrain_hdr_a[2];
extern unsigned short terrain_base_a;
extern void TerrainTileToCache(unsigned short tile, unsigned short x, unsigned short y);

/* @0x2bd00 */
void TerrainTileAdvanceA(int idx)
{
    unsigned short v;
    unsigned short off;
    unsigned t;
    unsigned short *p;

    v = (tile_map[idx] & 0x7ff) - terrain_base_a;
    if ((int)v < (*(long *)terrain_hdr_a >> 16)) {
        off = (unsigned short)(v + 1) * terrain_hdr_a[0];
    } else {
        off = 0;
    }
    off += *terrain_scan_table;
    t = (terrain_tbl_a[off] & 0xfff) + terrain_base_a - 1;
    p = tile_map + idx;
    t = t | (*p & 0xf800);
    *p = t;
    if ((int)map_scroll_x <= terrain_scan_x &&
        (int)map_scroll_y <= terrain_scan_y &&
        (int)map_scroll_x + 15 >= terrain_scan_x &&
        (int)map_scroll_y + 11 >= terrain_scan_y) {
        TerrainTileToCache(t, (unsigned short)terrain_scan_x, (unsigned short)terrain_scan_y);
    }
}
