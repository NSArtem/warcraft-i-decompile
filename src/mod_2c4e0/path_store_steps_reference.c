/* codegen-compiler: 10.0a */
#include "game_2c4e0.h"

extern signed char dir_dx[8];
extern signed char dir_dy[8];
extern unsigned char *map_cost;
extern Point path_start;

/* @0x2c8c0 */
void PathStoreSteps(unsigned char *path, short count, Point *to, unsigned char dir)
{
    Point cur;
    short i;
    unsigned char d;

    cur = path_start;
    i = 0;
    while (i < 20) {
        count--;
        if (count == -1) {
            break;
        }
        d = map_cost[(cur.y * 64 + cur.x) * 2 + dir];
        *path++ = d;
        cur.x += dir_dx[d];
        cur.y += dir_dy[d];
        i++;
        if (cur.x == to->x && cur.y == to->y) {
            break;
        }
    }
    while (i++ < 20) {
        *path++ = 0xfe;
    }
}
