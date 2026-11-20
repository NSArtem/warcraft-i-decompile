/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "game_2c4e0.h"

/* @0x2cc04 */
short PathDistance(Point *a, Point *b)
{
    short dx, dy;

    dx = a->x - b->x;
    dy = a->y - b->y;
    if (dx < 0) {
        dx = -dx;
    }
    if (dy < 0) {
        dy = -dy;
    }
    if (dx > dy) {
        dy = dx;
    }
    return dy;
}
