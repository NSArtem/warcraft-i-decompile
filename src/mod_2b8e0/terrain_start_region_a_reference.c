/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern short unit_type_size[][2];
extern unsigned short terrain_footprint_2x2[];
extern unsigned short terrain_footprint_2x3[];
extern unsigned short terrain_footprint_3x3_a[];
extern unsigned short terrain_footprint_default[];
extern int terrain_scan_w;
extern int terrain_scan_h;
extern int terrain_scan_y;
extern int terrain_scan_x;
extern void (*terrain_scan_cb)(int);
extern unsigned short *terrain_scan_table;
extern void TerrainWalkRegion(void);

/* @0x2bdd4 */
void TerrainStartRegionA(struct Unit *u)
{
    unsigned t;
    int w;

    terrain_scan_x = (*(long *)((char *)u + 8) >> 16) + 1;
    terrain_scan_y = (*(long *)((char *)u + 10) >> 16) + 1;
    t = *((unsigned char *)u + 0x1b);
    terrain_scan_h = ((long *)((char *)unit_type_size - 2))[t] >> 16;
    w = ((long *)unit_type_size)[t] >> 16;
    if (terrain_scan_h == 3 && w == terrain_scan_h) {
        terrain_scan_table = terrain_footprint_3x3_a;
    } else if (terrain_scan_h == 2 && w == terrain_scan_h) {
        terrain_scan_table = terrain_footprint_2x2;
    } else if (terrain_scan_h == 3 && w == 2) {
        terrain_scan_table = terrain_footprint_2x3;
    } else {
        terrain_scan_table = terrain_footprint_default;
        terrain_scan_x = (*(long *)((char *)u + 8) >> 16) + 2;
        terrain_scan_y = (*(long *)((char *)u + 10) >> 16) + 2;
    }
    terrain_scan_cb = TerrainTileAdvanceA;
    terrain_scan_w = w;
    TerrainWalkRegion();
}
