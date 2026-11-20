/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned short *terrain_tbl_d;
extern unsigned short *tile_map;
extern short step4_dx[4];
extern short step4_dy[4];
extern unsigned short terrain_hdr_d[2];
extern unsigned short terrain_base_d;

/* @0x2bbe4 */
int TerrainFindClearTile(unsigned short *p)
{
    unsigned short r;
    unsigned short d;
    unsigned short k;
    unsigned short v;

    for (r = 3; r < 10; r += 2) {
        p[0]--;
        p[1]--;
        for (d = 0; d < 4; d++) {
            for (k = 0; k < r; k++) {
                if (p[0] < 0x40 && p[1] < 0x40) {
                    v = (tile_map[((*(long *)p >> 16) << 6) + (short)p[0]] & 0x7ff) - terrain_base_d;
                    if (v < (*(long *)terrain_hdr_d >> 16) &&
                        (terrain_tbl_d[(unsigned short)(v + 1) * (*(long *)((char *)terrain_hdr_d - 2) >> 16)] & 0xf000) == 0) {
                        return 1;
                    }
                }
                p[0] += step4_dx[d];
                p[1] += step4_dy[d];
            }
            p[0] -= step4_dx[d];
            p[1] -= step4_dy[d];
        }
    }
    return 0;
}
