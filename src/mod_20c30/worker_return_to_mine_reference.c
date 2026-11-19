/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * WorkerReturnToMine (0x21df0, PLACEBOX.C): a peasant/peon that just
 * finished a building goes back to the mine on its tile.  The mine is looked
 * up with the ring search fn_2bbe4, which rewrites the tile.
 *
 * Source shape: nested tests with a single trailing `return 0` so all three
 * failure paths share the epilogue block at 0x21e4e, as in the original. */
#include "mod_20c30.h"

/* the coordinate arguments convert from short to int, so the original loads
 * them from the packed local as dwords (`mov ebx,[p+0]>>16`, `mov edx,[p-2]>>16`) */
void UnitOrderTarget(Unit *u, int x, int y, Unit *target, void (*cb)(Unit *));

/* @0x21df0 */
unsigned short WorkerReturnToMine(Unit *u)
{
    Point p;

    if (u->type >= 2 && u->type <= 3) {
        if (u->order_next2 == 0xa) {
            p = *(Point *)&u->tx;
            if (fn_2bbe4(&p) != 0) {
                UnitOrderTarget(u, p.x, p.y, 0, fn_21094);
                return UnitAdvanceOrder(u, 1);
            }
        }
    }
    return 0;
}
