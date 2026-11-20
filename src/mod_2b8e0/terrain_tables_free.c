/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern void *terrain_tbl_a;
extern void *terrain_tbl_b;
extern void *terrain_tbl_c;
extern void *terrain_tbl_d;
extern void GdsFree(void *p);

/* @0x2ba08 */
void TerrainTablesFree(void)
{
    GdsFree(terrain_tbl_a);
    terrain_tbl_a = 0;
    GdsFree(terrain_tbl_d);
    terrain_tbl_d = 0;
    GdsFree(terrain_tbl_b);
    terrain_tbl_b = 0;
    GdsFree(terrain_tbl_c);
    terrain_tbl_c = 0;
}
