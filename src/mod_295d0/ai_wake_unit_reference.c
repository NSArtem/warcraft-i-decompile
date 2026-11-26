/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiWakeUnit 0x29a9c: try to wake one of
 * the scenario's dormant units.  A dormant unit is a unit with the 0x200 flag
 * that the scenario placed on the map; this routine, at a 25% chance
 * (Random(0x18) & 3), finds a dormant non-building unit of the caller's owner
 * and type, copies its work point onto the caller and activates it
 * (flags = 1).  It returns 1 when a unit was woken.  See
 * docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x29a9c */
int AiWakeUnit(Unit *u)
{
    Unit *v;
    int i;
    unsigned found;

    if (ai_helper_count[u->owner] != 0) {
        found = 0;
        v = unit_array;
        for (i = 0; i < 200; i++) {
            if ((v->flags & 0x200) == 0)
                goto next1;
            if (v->owner != u->owner)
                goto next1;
            if (v->type >= 0x20 && v->type <= 0x32)
                goto next1;
            found = 1;
            break;
next1:
            v++;
        }
        ai_helper_count[u->owner] = found;
        if ((GameRandom(0x18) & 3) == 0)
            return 0;
    } else {
        if ((GameRandom(0x18) & 3) != 0)
            return 0;
    }
    v = unit_array;
    for (i = 0; i < 200; i++) {
        if ((v->flags & 0x200) == 0)
            goto next2;
        if (v->owner != u->owner)
            goto next2;
        if (v->type >= 0x20 && v->type <= 0x32)
            goto next2;
        if (v->word46 != u->type)
            goto next2;
        u->work_x = v->work_x;
        u->work_y = v->work_y;
        v->flags = 1;
        return 1;
next2:
        v++;
    }
    return 0;
}
