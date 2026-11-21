/* codegen-compiler: 10.0a */
#include "mod_2b1b0_c.h"

extern int terrain_scan_w;
extern int terrain_scan_h;
extern int terrain_scan_y;
extern void (*terrain_scan_cb)(int);
extern unsigned short *terrain_scan_table;
extern int terrain_scan_x;

/* @0x2b1b0 */
void TerrainWalkRegion(void)
{
    int x;
    unsigned short *tbl;
    int stride;
    int pos;
    int i;
    int j;
    int t;

    x = terrain_scan_x;
    tbl = terrain_scan_table;
    stride = terrain_scan_h;
    t = terrain_scan_y - terrain_scan_w / 2;
    terrain_scan_y = t;
    if (t < 0) {
        t = -t;
        terrain_scan_y = t;
        terrain_scan_w -= t;
        tbl += t * stride;
        terrain_scan_y = 0;
    } else {
        t = t + terrain_scan_w - 0x40;
        if (t > 0) {
            terrain_scan_w -= t;
        }
    }
    x -= terrain_scan_h / 2;
    if (x < 0) {
        x = -x;
        terrain_scan_h -= x;
        tbl += x;
        x = 0;
    } else {
        t = x + terrain_scan_h - 0x40;
        if (t > 0) {
            terrain_scan_h -= t;
        }
    }
    pos = (terrain_scan_y << 6) + x;
    for (i = 0; i < terrain_scan_w; i++) {
        for (j = 0; j < terrain_scan_h; j++) {
            terrain_scan_x = x;
            terrain_scan_table = tbl;
            terrain_scan_cb(pos);
            tbl = terrain_scan_table;
            x = terrain_scan_x + 1;
            pos++;
            tbl++;
        }
        x -= terrain_scan_h;
        terrain_scan_y++;
        pos += 0x40 - terrain_scan_h;
        tbl += stride - terrain_scan_h;
    }
    terrain_scan_table = tbl;
    terrain_scan_x = x;
}
