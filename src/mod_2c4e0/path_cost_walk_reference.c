/* codegen-compiler: 10.0a */
#include "game_2c4e0.h"

extern signed char dir_dx[8];
extern signed char dir_dy[8];
extern unsigned char dat_55224[];
extern unsigned char *map_cost;
extern Point path_start;

/* @0x2c790 */
int PathCostWalk(Point *from, Point *to)
{
    Point cur, nxt;
    int count, changed;
    unsigned char d, d2, r;

    for (;;) {
        changed = 0;
        count = 0;
        cur = path_start;
        for (;;) {
            if (cur.x == to->x && cur.y == to->y) {
                break;
            }
            count++;
            d = map_cost[(cur.y * 64 + cur.x) * 2];
            nxt = cur;
            nxt.x += dir_dx[d];
            nxt.y += dir_dy[d];
            if (nxt.x == to->x && nxt.y == to->y) {
                break;
            }
            d2 = map_cost[(nxt.y * 64 + nxt.x) * 2];
            r = dat_55224[d * 8 + d2];
            if (r > 7) {
                cur = nxt;
                continue;
            }
            map_cost[(cur.y * 64 + cur.x) * 2] = r;
            changed = 1;
            cur.x = nxt.x + dir_dx[d2];
            cur.y = nxt.y + dir_dy[d2];
        }
        if (changed == 0) {
            break;
        }
    }
    return count;
}
