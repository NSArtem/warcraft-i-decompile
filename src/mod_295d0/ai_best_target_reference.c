/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiBestTarget 0x29fec: the AI's target
 * picker.  Scans the 200 units for a live enemy of the caller's side inside
 * `range` of `origin` (measured by fn_13270), preferring non-buildings over
 * buildings and units inside `pref_dist`, and keeping the highest
 * target_priority[type].  `enemy_row` is the caller's hostility row.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x29fec */
Unit *AiBestTarget(short *origin, short range, short pref_dist, unsigned char *enemy_row)
{
    Unit *u = unit_array;
    Unit *best = 0;
    short best_dist = -1;
    unsigned short best_prio = 0;
    int i;

    for (i = 0; i < 200; i++) {
        unsigned short dist;
        unsigned short prio;
        int prefer;

        if ((u->flags & 0x207) != 0)
            goto next;
        if (enemy_row[u->owner] == 0)
            goto next;
        if (u->timer36 != 0)
            goto next;
        dist = fn_13270(origin, u);
        if (dist > range)
            goto next;
        prio = target_priority[u->type];
        prefer = 0;
        if (best != 0 && best->type >= 0x20 && best->type <= 0x32) {
            if (u->type < 0x20 || u->type > 0x32)
                prefer = 1;
        }
        if (!prefer && best_dist > pref_dist && dist <= pref_dist)
            prefer = 1;
        if (prefer)
            best_prio = 0;
        if (best_prio >= prio)
            goto next;
        best_prio = prio;
        best_dist = dist;
        best = u;
next:
        u++;
    }
    return best;
}
