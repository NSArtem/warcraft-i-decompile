/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x287f0 - remember the hp and health fraction of every selected unit so the
 * "changed?" callbacks can tell whether the panel needs a repaint. */
#include "status.h"

void StatusPanelCacheUnitState(void)
{
    Unit *u;
    unsigned long i;

    u = SelectionFirst();
    if (u != 0) {
        i = 0;
        do {
            status_hp_cache[i] = u->hp;
            status_damage_cache[i] = u->damage;
            u = SelectionNext();
            i++;
        } while (u != 0);
    }
}
