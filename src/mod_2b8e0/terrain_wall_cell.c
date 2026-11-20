/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern void *terrain_tbl_b;
extern unsigned short terrain_wall_autotile_map[];
extern unsigned short terrain_hdr_b[2];
extern unsigned short terrain_base_b;
extern unsigned short terrain_autotile_step;
extern unsigned short *terrain_autotile_base;
extern unsigned short *terrain_autotile_map;
extern unsigned short terrain_autotile_stride;
extern unsigned short terrain_autotile_first;
extern unsigned short terrain_flag_mask;

/* @0x2c268 */
void TerrainWallCell(int x, int y)
{
    terrain_flag_mask = 0x10;
    terrain_autotile_map = terrain_wall_autotile_map;
    terrain_autotile_base = (unsigned short *)terrain_tbl_b;
    terrain_autotile_stride = terrain_hdr_b[0];
    terrain_autotile_first = terrain_base_b;
    terrain_autotile_step = 3;
    TerrainAutotileCell(x, y, 0x10);
    terrain_autotile_step = 0;
}
