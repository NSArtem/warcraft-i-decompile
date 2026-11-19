/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiCastHeal 0x2a270: the Cleric's heal.
 * Scans the 21x21 tiles around the unit for the friendly non-building unit
 * with the largest hp deficit and casts spell 0x11 (healing) on it.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x2a270 */
int AiCastHeal(Unit *u)
{
    int x, y, w, h;
    Unit **cell;
    Unit *best = 0;
    int best_missing = -1;
    int i, j;

    x = u->tx;
    y = u->ty;
    ClipBox(&x, &y, &w, &h, 0x15);
    cell = &object_map[y * 64 + x];
    for (i = 0; i < h; i++) {
        for (j = 0; j < w; j++) {
            Unit *v = *cell++;
            int missing;
            if (v == 0)
                continue;
            if (hostility[u->owner * 5 + v->owner] != 0)
                continue;
            if (v->type >= 0x20 && v->type <= 0x32)
                continue;
            if ((v->flags & 0x207) != 0)
                continue;
            if (v->hp == unit_max_hp[v->type])
                continue;
            missing = unit_max_hp[v->type] - v->hp;
            if (missing <= best_missing)
                continue;
            best_missing = missing;
            best = v;
        }
        cell += 0x40 - w;
    }
    if (best == 0)
        return 0;
    spell_order = 0x11;
    UnitOrderTarget(u, 0, 0, best, fn_21168);
    return 1;
}
