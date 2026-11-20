/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern int terrain_scan_x;
extern int terrain_scan_y;
extern int terrain_scan_w;
extern int terrain_scan_h;
extern unsigned short terrain_footprint_3x3_b[];
extern unsigned short *terrain_scan_table;
extern void (*terrain_scan_cb)(int);
extern void TerrainWalkRegion(void);

/* @0x2bb38 */
void TerrainStartRegionB(struct Unit *u)
{
    terrain_scan_x = *(long *)((char *)u + 0x4c) >> 16;
    terrain_scan_y = *(long *)((char *)u + 0x4e) >> 16;
    terrain_scan_w = 3;
    terrain_scan_h = 3;
    terrain_scan_table = terrain_footprint_3x3_b;
    terrain_scan_cb = TerrainTileAdvanceB;
    TerrainWalkRegion();
}
