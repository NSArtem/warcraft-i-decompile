/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiAcquireNearbyTarget 0x2a0e0: look for
 * an enemy near the unit.  The search radius is 4 when the unit is attacking
 * (order flag 8) and 8 otherwise; the siege types 4/5 use their own sight
 * range plus 2.  See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

extern Unit *AiBestTarget(short *origin, short range, short pref_dist, unsigned char *enemy_row);

/* @0x2a0e0 */
Unit *AiAcquireNearbyTarget(Unit *u)
{
    int type = u->type;
    int range;

    if (type >= 4 && type <= 5) {
        range = unit_sight_range[type] + 2;
    } else if ((u->order_flags & 8) != 0) {
        range = 4;
    } else {
        range = 8;
    }
    return AiBestTarget(&u->tx, range, unit_sight_range[u->type],
                        &hostility[u->owner * 5]);
}
