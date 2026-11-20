/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned short *terrain_tbl_d;
extern unsigned short *tile_map;
extern unsigned short terrain_hdr_d[2];
extern unsigned short terrain_base_d;

/* @0x2bb7c */
int TerrainTileIsClear(short *pt)
{
    unsigned short v;

    v = (tile_map[pt[0] + ((*(long *)pt >> 16) << 6)] & 0x7ff) - terrain_base_d;
    if (v >= (*(long *)terrain_hdr_d >> 16)) {
        return 0;
    }
    v++;
    return (terrain_tbl_d[(*(long *)((char *)terrain_hdr_d - 2) >> 16) * v] & 0xf000) == 0;
}
