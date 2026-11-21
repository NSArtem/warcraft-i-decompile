/* codegen-compiler: 10.0a */
#include "mod_1e9a0.h"

extern int terrain_scan_x;
extern int terrain_scan_y;
extern int terrain_scan_w;
extern int terrain_scan_h;
extern unsigned short *terrain_scan_table;
extern void (*terrain_scan_cb)(int);
extern void TerrainWalkRegion(void);

/* @0x1eb18 */
void FogUpdateArea9(short x, short y, unsigned short owner)
{
    fog_cur_owner = owner;
    terrain_scan_x = x;
    terrain_scan_y = y;
    terrain_scan_w = 9;
    terrain_scan_h = 9;
    terrain_scan_table = fog_shape_9;
    terrain_scan_cb = FogUpdateTile;
    TerrainWalkRegion();
}
