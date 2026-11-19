/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * OrderClampDest (0x220e8, PLACEBOX.C): when the order's target is a
 * building, centre the unit's destination on the building's tile and clamp it
 * to within half the building's width/height of the unit's own tile, so a
 * worker walks up to the side of the building it is going to work on.
 * Only caller: OrderTargetInRange 0x22262. */
#include "mod_20c30.h"

/* @0x220e8 */
void OrderClampDest(Unit *u)
{
    Unit *t = u->target;
    int w2, h2, e1, e2, a, b, utx, uty;

    if (t == 0)
        return;
    a = t->tx;
    b = t->ty;
    if (t->type < 0x20 || t->type > 0x32) {
        u->dest_x = a;
        u->dest_y = b;
        return;
    }
    w2 = unit_type_size[t->type * 2];
    e1 = (w2 & 1) == 0;
    w2 = (unsigned short)w2 >> 1;
    h2 = unit_type_size[t->type * 2 + 1];
    e2 = (h2 & 1) == 0;
    h2 = (unsigned short)h2 >> 1;
    a += w2;
    utx = u->tx;
    if (utx > a - w2) {
        if (w2 + a > utx)
            a = w2 + a - e1;
    } else {
        a -= w2;
    }
    u->dest_x = a;
    b += h2;
    uty = u->ty;
    if (uty > b - h2) {
        if (h2 + b > uty)
            b = h2 + b - e2;
    } else {
        b -= h2;
    }
    u->dest_y = b;
}
