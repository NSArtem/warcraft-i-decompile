/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for the "does the panel need a repaint?" callbacks of
 * STATUS.C: UnitPanelStateChanged 0x281f4, FarmPanelChanged 0x28254,
 * GoldMinePanelChanged 0x28360 and WorkerPanelChanged 0x28400.  These are the
 * `changed` field of the unit_panel_table entries (0x549c4 + 14*type, +6);
 * UnitPanelUpdate 0x29450 calls them before repainting. */
#include "status.h"

/* 0x281f4 - the standard callback: any selected unit whose hp or health
 * fraction differs from the cached value, or a different unit type than the
 * one on show, means "repaint".  The caches are refreshed by
 * StatusPanelCacheUnitState 0x287f0. */
unsigned short UnitPanelStateChanged(void)
{
    Unit *u;
    unsigned long i;
    unsigned long damage;

    u = SelectionFirst();
    if (u != 0) {
        i = 0;
        do {
            if (u->hp != status_hp_cache[i])
                return 1;
            damage = u->damage;
            if (damage != status_damage_cache[i])
                return 1;
            u = SelectionNext();
            i++;
        } while (u != 0);
    }
    return status_unit->type_copy != status_unit_type;
}

/* 0x28254 - the farm panel (types 0x20/0x21): the "used" number (active men
 * minus summoned creatures) and the "grown" capacity, then the standard
 * callback. */
unsigned short FarmPanelChanged(void)
{
    unsigned long used;
    unsigned long cached;

    used = player_active_men[0] - player_summoned[0];
    cached = status_men_used;
    if (cached != used)
        return 1;
    if (status_men_grown != player_food[0])
        return 1;
    return UnitPanelStateChanged();
}

