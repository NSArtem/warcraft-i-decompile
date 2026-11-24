/* codegen-compiler: 10.0a */
#include "game_2c4e0.h"

extern short unit_type_size[52][2];
extern unsigned short *map_flags;
extern Point path_dest;

/* @0x2cb2c */
void PathBlockArea(int mask, Unit *u)
{
    unsigned short x, y;
    unsigned short idx;
    short w, h, i, j;
    unsigned short *fp;

    if (u != 0) {
        x = u->tx - 1;
        y = u->ty - 1;
        w = unit_type_size[u->type][0] + 2;
        h = unit_type_size[u->type][1] + 2;
    } else {
        x = path_dest.x - 1;
        y = path_dest.y - 1;
        w = 3;
        h = 3;
    }
    for (i = 0; i < h; i++) {
        idx = (unsigned short)(y * 64 + x);
        for (j = 0; j < w; j++) {
            if (x < 0x40 && y < 0x40) {
                fp = map_flags + idx;
                ((unsigned char *)fp)[1] |= 0xc0;
                *fp &= (unsigned short)mask;
            }
            idx++;
            x++;
        }
        x -= w;
        y++;
    }
}
