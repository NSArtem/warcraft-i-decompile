/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiChooseBuilding 0x2ad10: choose which
 * of the AI's buildings a worker should (re)build.  A destroyed building (flag
 * 0x200) is chosen from the down table, a healthy standing one (hp >= 3/4)
 * from the up table; when the owner is low on gold/lumber only a town hall
 * (0x28/0x29) is considered.  See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x2ad10 */
Unit *AiChooseBuilding(Unit *u)
{
    int poor;
    Unit *v = unit_array;
    Unit *best = 0;
    unsigned short best_prio = 0;
    int i;

    poor = dat_50074[u->owner] < 0xc8 && dat_50060[u->owner] < 0x64;
    for (i = 0; i < 200; i++) {
        unsigned short prio;

        if ((v->flags & 7) != 0)
            goto next;
        if (v->owner != u->owner)
            goto next;
        if (v->type < 0x20 || v->type > 0x32)
            goto next;
        if (poor && v->type != 0x28 && v->type != 0x29)
            goto next;
        if ((v->flags & 0x200) != 0) {
            if (v->word4a != 0)
                goto next;
            prio = building_priority_down[v->type];
        } else {
            if (v->hp < unit_max_hp[v->type] * 3 / 4)
                goto next;
            prio = building_priority_up[v->type];
        }
        if (best_prio >= prio)
            goto next;
        best_prio = prio;
        best = v;
next:
        v++;
    }
    return best;
}
