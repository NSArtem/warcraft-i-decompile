/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned short map_scroll_x;
extern unsigned short map_scroll_y;
extern void *terrain_tbl_b;
extern unsigned char *map_flags;
extern char *tile_map;
extern unsigned short terrain_hdr_b[2];
extern unsigned short terrain_base_b;
extern unsigned short terrain_wall_recurse;
extern void TerrainTileToCache(unsigned short tile, unsigned short x, unsigned short y);

/* @0x2c2c4 */
void TerrainWallAdvance(int x, int y)
{
    int off;
    unsigned short *tp;
    unsigned short i;
    unsigned short e;
    unsigned short t;
    unsigned short nt;

    off = (y * 0x40 + x) * 2;
    tp = (unsigned short *)(tile_map + off);
    i = (*tp & 0x7ff) - terrain_base_b;
    if ((*(long *)&terrain_hdr_b[0] >> 16) > (int)i) {
        i = i + 1;
        e = *((unsigned short *)terrain_tbl_b +
              (*(long *)((char *)&terrain_hdr_b[0] - 2) >> 16) * i + 1);
        t = e & 0xfff;
        if (i != t) {
            nt = (t + terrain_base_b - 1) | (*tp & 0xf800);
            *tp = nt;
            if ((e & 0x1000) == 0) {
                map_flags[off] &= 0xe3;
            }
            if (terrain_wall_recurse != 0 && (e & 0x2000) != 0) {
                terrain_wall_recurse = 0;
                TerrainWallAdvance(x, y - 1);
                TerrainWallAdvance(x, y + 1);
                terrain_wall_recurse = 1;
            }
            if (x >= map_scroll_x && y >= map_scroll_y &&
                x <= map_scroll_x + 0xf && y <= map_scroll_y + 0xb) {
                TerrainTileToCache(nt, x, y);
            }
        }
    }
}
