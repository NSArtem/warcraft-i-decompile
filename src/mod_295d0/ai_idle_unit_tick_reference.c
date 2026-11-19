/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiIdleUnitTick 0x2ab54: what an idle AI
 * unit does - attack the best nearby target (clearing the attack flag), then
 * defend the town hall, then return to the AI attack point (order flag 4) or
 * its work point, and otherwise stay near the start area.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

extern Unit *AiAcquireNearbyTarget(Unit *u);   /* 0x2a0e0 */
extern Unit *AiDefendTownHall(Unit *u);        /* 0x2a168 */
extern int AiGuardStartArea(Unit *u);          /* 0x29f40 */

/* @0x2ab54 */
void AiIdleUnitTick(Unit *u)
{
    Unit *t;

    t = AiAcquireNearbyTarget(u);
    if (t != 0) {
        UnitOrderTarget(u, 0, 0, t, fn_20f30);
        if ((u->order_flags & 8) != 0)
            u->order_flags = 4;
        return;
    }
    t = AiDefendTownHall(u);
    if (t != 0) {
        UnitOrderTarget(u, 0, 0, t, fn_20f30);
        return;
    }
    if ((u->order_flags & 4) != 0) {
        UnitOrderTarget(u, ai_attack_point.x, ai_attack_point.y, 0, fn_20f30);
        return;
    }
    if ((u->order_flags & 0x18) != 0)
        goto guard;
    if (u->work_x == u->tx && u->work_y == u->ty)
        goto guard;
    UnitOrderTarget(u, u->work_x, u->work_y, 0, fn_20f30);
    return;
guard:
    AiGuardStartArea(u);
}
