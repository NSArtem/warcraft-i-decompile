/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * UnitIsPassable (0x21e58, PLACEBOX.C): the pathing predicate "this unit does
 * not block its tile".  PathScan/PathTrace skip a unit when it returns 1. */
#include "mod_20c30.h"

/* @0x21e58 */
unsigned short UnitIsPassable(Unit *u)
{
    if ((u->flags.w & 0x207) != 0)
        return u->type <= 0x1f;
    if (u->order != 3 && u->order != 0xc)
        return 0;
    if ((u->flags2 & 0xf000) != 0)
        return 0;
    if ((u->flags.w & 0x1000) != 0)
        return 0;
    return 1;
}
