/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern void *terrain_tbl_b;
extern unsigned short terrain_wall_autotile_map[];
extern unsigned short *tile_map;
extern unsigned short terrain_hdr_b[2];
extern unsigned short terrain_base_b;
extern unsigned short *terrain_autotile_base;
extern unsigned short *terrain_autotile_map;
extern unsigned short terrain_autotile_stride;
extern unsigned short terrain_autotile_first;
extern unsigned short terrain_flag_mask;

/* @0x2c14c */
void TerrainApplyCellFlags(int x, int y, unsigned short flags)
{
    unsigned char *p;
    unsigned char b;

    terrain_flag_mask = 0xc;
    terrain_autotile_map = terrain_wall_autotile_map;
    terrain_autotile_base = (unsigned short *)terrain_tbl_b;
    terrain_autotile_stride = terrain_hdr_b[0];
    terrain_autotile_first = terrain_base_b;
    TerrainAutotileCross(x, y, flags);
    p = (unsigned char *)tile_map;
    b = p[(x + y * 0x40) * 2 + 1] & 7;
    p[(x + y * 0x40) * 2 + 1] = b | 0xa0;
}
