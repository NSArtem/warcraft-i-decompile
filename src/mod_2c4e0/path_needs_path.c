/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "game_2c4e0.h"

extern Point path_dest;
extern unsigned short path_distance;
extern short PathDistance(Point *a, Point *b);

/* @0x2cc2c */
short PathNeedsPath(Point *p)
{
    int a;
    int b;

    a = path_distance;
    b = (unsigned short)PathDistance(p, &path_dest);
    return a + 8 < b;
}
