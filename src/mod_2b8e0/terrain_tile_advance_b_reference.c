/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned short map_scroll_x;
extern unsigned short map_scroll_y;
extern unsigned short *terrain_tbl_d;
extern unsigned short *map_flags;
extern unsigned short *tile_map;
extern int terrain_scan_y;
extern int terrain_scan_x;
extern unsigned short *terrain_scan_table;
extern unsigned short terrain_hdr_d[2];
extern unsigned short terrain_base_d;
extern void TerrainTileToCache(unsigned short tile, unsigned short x, unsigned short y);

/* @0x2ba50 */
void TerrainTileAdvanceB(int idx)
{
    unsigned short *p;
    unsigned short *q;
    unsigned short v;
    unsigned short t;

    p = tile_map + idx;
    v = (*p & 0x7ff) - terrain_base_d;
    if (v < (*(long *)terrain_hdr_d >> 16)) {
        q = terrain_tbl_d + (unsigned short)((unsigned short)(v + 1) * terrain_hdr_d[0] + *terrain_scan_table);
        t = (*q & 0xfff) + terrain_base_d - 1;
        t = t | (*p & 0xf800);
        *p = t;
        if ((*q & 0xf000) != 0) {
            ((unsigned char *)map_flags)[idx * 2] &= 0x7f;
        }
        if ((int)map_scroll_x <= terrain_scan_x &&
            (int)map_scroll_y <= terrain_scan_y &&
            (int)map_scroll_x + 15 >= terrain_scan_x &&
            (int)map_scroll_y + 11 >= terrain_scan_y) {
            TerrainTileToCache(t, (unsigned short)terrain_scan_x, (unsigned short)terrain_scan_y);
        }
    }
}
