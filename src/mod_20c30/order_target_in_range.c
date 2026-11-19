/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * fn_2220c (0x2220c, PLACEBOX.C) = OrderTargetInRange: is the (clamped)
 * destination within the order's range?  Range comes from order_range
 * (0x52b04); 0xff means "the unit's sight range", and for a target-less move
 * that only applies when the destination tile is a legal walk target.
 * Resets the path and returns 1 when in range.  The symbol entry lives in
 * mod_104b0.toml (placeholder fn_2220c); reported, not wired here. */
#include "mod_20c30.h"

unsigned short fn_13348(short x, short y, unsigned mask);   /* 0x13348 */
void UnitResetPath(Unit *u);                           /* 0x2cebc */
void OrderClampDest(Unit *u);                          /* 0x220e8 */

/* @0x2220c */
unsigned short fn_2220c(Unit *u, unsigned char arg)
{
    unsigned short range;
    short dx, dy;

    range = order_range[arg];
    if (range == 0xff) {
        if (u->target != 0 || fn_13348(u->dest_x, u->dest_y, 0xc) != 0)
            range = unit_sight_range[u->type];
        else
            range = 0;
    }
    OrderClampDest(u);
    dx = u->dest_x - u->tx;
    if (dx < 0)
        dx = -dx;
    dy = u->dest_y - u->ty;
    if (dy < 0)
        dy = -dy;
    if (dx > range || dy > range)
        return 0;
    UnitResetPath(u);
    return 1;
}
