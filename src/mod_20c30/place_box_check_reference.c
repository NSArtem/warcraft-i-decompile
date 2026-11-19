/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * PlaceBoxCheck (0x2256c, PLACEBOX.C): can the selected worker place `type`
 * at tile p?  Returns a 0..5 code that indexes place_error (0 = fine).
 * Road (0x34) and wall (0x35) have their own checks; everything else is a
 * building check.  The worker's own tile is treated as free during the test
 * (its occupancy bit is cleared and restored). */
#include "mod_20c30.h"

unsigned short fn_13360(short x, short y);              /* 0x13360 road */
unsigned short fn_1346c(short x, short y);              /* 0x1346c wall */
unsigned short fn_1357c(short x, short y);              /* 0x1357c building */

/* @0x2256c */
unsigned short PlaceBoxCheck(Point p, unsigned char type)
{
    Unit *w;
    unsigned short r;

    w = SelectionFirst();
    if (w != 0 && w->type >= 2 && w->type <= 3)
        map_flags[(w->ty << 6) + w->tx] &= 0xfeff;
    if (type == PLACE_ROAD)
        r = fn_13360(p.x, p.y);
    else if (type == PLACE_WALL)
        r = fn_1346c(p.x, p.y);
    else
        r = fn_1357c(p.x, p.y);
    if (w != 0 && w->type >= 2 && w->type <= 3)
        map_flags[(w->ty << 6) + w->tx] |= 0x100;
    return r;
}
