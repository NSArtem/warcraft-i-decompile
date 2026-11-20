/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned short scenario_tileset_id;
extern void *terrain_tbl_a;
extern void *terrain_tbl_b;
extern void *terrain_tbl_c;
extern void *terrain_tbl_d;
extern unsigned short terrain_hdr_a[2];
extern unsigned short terrain_hdr_b[2];
extern unsigned short terrain_hdr_c[2];
extern unsigned short terrain_hdr_d[2];
extern unsigned short terrain_base_c;
extern unsigned short terrain_base_b;
extern unsigned short terrain_base_d;
extern unsigned short terrain_base_a;

/* @0x2b91c */
void TerrainTablesInit(void)
{
    unsigned short b, d, c, a;

    if (scenario_tileset_id == 0xc0) {
        b = 0xc9;
        a = 0xc8;
        c = 0xca;
        d = 0xcb;
    } else if (scenario_tileset_id == 0xc3) {
        b = 0xcd;
        a = 0xcc;
        c = 0xce;
        d = 0xcf;
    } else {
        b = 0xd1;
        a = 0xd0;
        c = 0xd2;
        d = 0xd3;
    }
    TerrainTableLoad(b, &terrain_tbl_b, terrain_hdr_b);
    TerrainTableLoad(a, &terrain_tbl_a, terrain_hdr_a);
    TerrainTableLoad(c, &terrain_tbl_c, terrain_hdr_c);
    TerrainTableLoad(d, &terrain_tbl_d, terrain_hdr_d);
    terrain_base_b = 10;
    terrain_base_a = terrain_hdr_b[1] + 10;
    terrain_base_c = terrain_base_a + terrain_hdr_a[1];
    terrain_base_d = terrain_base_c + terrain_hdr_c[1];
}
