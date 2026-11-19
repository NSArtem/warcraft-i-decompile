/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * UnitOrderTargetFinish (0x22464, PLACEBOX.C): the tail of UnitOrderTarget
 * (0x2e140).  Clears the path and the flags2 nibble, clamps the destination,
 * drops a dead target, and decides whether a two-step order (move then
 * attack/build) runs its second step now. */
#include "mod_20c30.h"

void UnitResetPath(Unit *u);                           /* 0x2cebc */
unsigned short fn_2207c(Unit *u);  /* UnitClearTargets, 0x2207c */
unsigned short fn_2220c(Unit *u, unsigned char arg);   /* OrderTargetInRange, 0x2220c */
void UnitSetNextOrder(Unit *u, unsigned char order);   /* 0x2eeac */
void PathSetReachableDest(Unit *u);                    /* 0x223bc */

/* @0x22464 */
void UnitOrderTargetFinish(Unit *u)
{
    UnitResetPath(u);
    ((unsigned char *)u)[0xf] &= 0xf;
    if (u->order_next2 != 0x12)
        PathSetReachableDest(u);
    if (fn_2207c(u) == 0) {
        UnitSetNextOrder(u, 2);
        return;
    }
    if ((order_props[u->order_next2] & 2) != 0) {
        if (u->order_next2 != 0x1f)
            UnitSetNextOrder(u, u->order_next2);
        return;
    }
    if (u->order_next != 0x1f && fn_2220c(u, u->order_next2) == 0)
        return;
    if (u->order_next2 != 0x1f)
        UnitSetNextOrder(u, u->order_next2);
}
