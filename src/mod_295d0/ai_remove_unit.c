/* codegen-compiler: 10.0a */
/* mod_295d0.  AiRemoveUnit 0x29ea8: drop a removed AI unit from the AI's
 * counters.  Called by UnitRemove 0x2e14c for every unit it takes off the map;
 * only AI units (player type 1) have counters.  A worker leaves the busy/work
 * counter of its order flags, any other unit releases its work site.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x29ea8 */
void AiRemoveUnit(Unit *u)
{
    int type;

    if (dat_5008c[u->owner] != 1)
        return;
    type = u->type;
    if (type >= 2 && type <= 3) {
        if ((u->order_flags & 2) != 0) {
            ai_busy_count[u->owner]--;
            return;
        }
        if ((u->order_flags & 1) != 0)
            ai_work_count[u->owner]--;
        return;
    }
    if ((u->work_site & 0x4000) == 0)
        return;
    work_sites[u->work_site & 0x3fff]--;
    u->work_site = 0;
}
