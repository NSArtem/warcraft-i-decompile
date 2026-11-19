/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * PathSetReachableDest (0x223bc, PLACEBOX.C): walk the path trace backwards
 * from the destination toward the unit and stop at the last walkable tile, so
 * a move order ends somewhere the unit can actually stand.  Called from
 * UnitOrderTargetFinish for a target-less order. */
#include "mod_20c30.h"

unsigned short fn_13348(short x, short y, unsigned mask);   /* 0x13348 */
void fn_1df0c(Point start, Point dest, void *trace);   /* 0x1df0c */
void fn_1df94(void *trace, Point *a, Point *b);        /* 0x1df94 */

/* @0x223bc */
void PathSetReachableDest(Unit *u)
{
    Point cur, d1, d2;
    char trace[8];

    if (u->target != 0)
        return;
    d1 = *(Point *)&u->tx;      /* zeroed dwords; overwritten by fn_1df94 */
    d2 = d1;
    d1.x = 0;
    d1.y = 0;
    d2.x = 0;
    d2.y = 0;
    cur = *(Point *)&u->dest_x;
    fn_1df0c(*(Point *)&u->tx, cur, trace);
    while (cur.x != u->tx || cur.y != u->ty) {
        if (fn_13348(cur.x, cur.y, 0x3cc) != 0) {
            fn_1df94(trace, &d2, &d1);
            cur.x -= d2.x;
            cur.y -= d1.x;
        } else {
            cur.x += d2.x;
            cur.y += d1.x;
            *(Point *)&u->dest_x = cur;
            return;
        }
    }
}
