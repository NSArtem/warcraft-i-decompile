/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * TileOccupiedByUnit (0x21ec0, PLACEBOX.C): "the move order's destination
 * tile is settled".  MoveOrderTick uses a non-zero result to keep the path
 * instead of resetting it.  Truth table in the area notes. */
#include "mod_20c30.h"

int PathPeekStep(Unit *u, Point *out);                 /* 0x2c4e0 */

/* @0x21ec0 */
unsigned short TileOccupiedByUnit(Unit *u, Point *p)
{
    Unit *obj;
    unsigned short idx;
    Point step;

    idx = (p->y << 6) + p->x;
    if ((map_flags[idx] & 0x100) == 0)
        return 0;
    obj = object_map[idx];
    if ((obj->flags.w & 0x207) != 0)
        return 1;
    if (hostility[u->owner * 5 + obj->owner] != 0)
        return 0;
    if (UnitIsPassable(obj) == 0)
        return 0;
    if (obj->order != 3)
        return 0;
    if (PathPeekStep(obj, &step) == 0)
        return 0;
    if (step.x != u->tx)
        return 1;
    if (step.y != u->ty)
        return 1;
    return 0;
}
