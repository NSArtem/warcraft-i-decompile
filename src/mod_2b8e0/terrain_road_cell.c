/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern void *terrain_tbl_c;
extern unsigned short terrain_road_autotile_map[];
extern unsigned short terrain_hdr_c[2];
extern unsigned short terrain_base_c;
extern unsigned short *terrain_autotile_base;
extern unsigned short *terrain_autotile_map;
extern unsigned short terrain_autotile_stride;
extern unsigned short terrain_autotile_first;
extern unsigned short terrain_flag_mask;

/* @0x2c100 */
void TerrainRoadCell(int x, int y, unsigned short mask)
{
    terrain_flag_mask = 3;
    terrain_autotile_map = terrain_road_autotile_map;
    terrain_autotile_base = (unsigned short *)terrain_tbl_c;
    terrain_autotile_stride = terrain_hdr_c[0];
    terrain_autotile_first = terrain_base_c;
    TerrainAutotileCross(x, y, mask);
}
