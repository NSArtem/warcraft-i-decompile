/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned short map_scroll_x;             /* 0x500d0 */
extern unsigned short map_scroll_y;             /* 0x500d2 */
extern unsigned short terrain_autotile_step;    /* 0x55204 */
extern unsigned short *map_flags;               /* 0x5857c */
extern unsigned short *tile_map;                /* 0x58584 */
extern unsigned short *terrain_autotile_base;   /* 0x5a450 */
extern unsigned short *terrain_autotile_map;    /* 0x5a454 */
extern unsigned short terrain_autotile_stride;  /* 0x5a45c */
extern unsigned short terrain_autotile_first;   /* 0x5a45e */
extern unsigned short terrain_flag_mask;        /* 0x5a460 */
extern void TerrainTileToCache(unsigned short tile, unsigned short x, unsigned short y); /* 0x1246c */

/* @0x2bf64 */
void TerrainAutotileCell(unsigned x, unsigned y, unsigned short flags)
{
    int idx;
    int n;
    unsigned short *pf;
    unsigned short *pt;
    unsigned short v;
    unsigned short t;
    unsigned short nt;

    if (x < 0x40 && y < 0x40) {
        idx = y * 0x40 + x;
        if (flags != 0xffff) {
            pf = map_flags + idx;
            v = *pf | flags;
            if ((v & terrain_flag_mask) == 0) {
                return;
            }
            if (flags != 0) {
                *pf = (v & 0xfff0) | flags;
            }
        }
        n = TerrainFlagTest(x, y + 1, idx + 0x40) * 2;
        n = (n | TerrainFlagTest(x + 1, y, idx + 1)) * 2;
        n = (n | TerrainFlagTest(x - 1, y, idx - 1)) * 2;
        n = n | TerrainFlagTest(x, y - 1, idx - 0x40);
        t = terrain_autotile_map[(unsigned short)n] * terrain_autotile_stride + terrain_autotile_step;
        t = terrain_autotile_base[t] & 0xfff;
        pt = tile_map + idx;
        nt = (t + terrain_autotile_first - 1) | (*pt & 0xf800);
        if (nt != *pt) {
            *pt = nt;
            if ((int)x >= map_scroll_x && (int)y >= map_scroll_y &&
                (int)x <= map_scroll_x + 0xf && (int)y <= map_scroll_y + 0xb) {
                TerrainTileToCache(nt, x, y);
            }
        }
    }
}
