/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_1e9a0.h"

extern int terrain_scan_x;
extern int terrain_scan_y;
extern int terrain_scan_w;
extern int terrain_scan_h;
extern unsigned short *terrain_scan_table;
extern void (*terrain_scan_cb)(int);
extern void TerrainWalkRegion(void);

/* @0x1ea58 */
void FogUpdateArea6(short x, short y, unsigned short owner)
{
    fog_cur_owner = owner;
    terrain_scan_x = x;
    terrain_scan_y = y;
    terrain_scan_w = 6;
    terrain_scan_h = 6;
    terrain_scan_table = fog_shape_6;
    terrain_scan_cb = FogUpdateTile;
    TerrainWalkRegion();
}
