/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitConsiderTarget (0x10834): score one candidate for UnitAcquireTarget.
 * The candidate must be a live map unit the searching player can see, not
 * already engaged, inside the search radius, and it must beat the best score
 * so far (priority - distance^2); the winner is left in target_search.best.
 * See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c */
extern unsigned char target_priority[];        /* 0x51d28 */
extern signed char dir_dx[];
extern signed char dir_dy[];

struct TargetSearch {
    Unit *best;                  /* 0x58540 */
    unsigned char *enemy_map;    /* 0x58544 */
    Point origin;                /* 0x58548 */
    short best_score;            /* 0x5854c */
    short flag_4e;               /* 0x5854e */
    short range;                 /* 0x58550 */
    short chase;                 /* 0x58552 */
    short min_range;             /* 0x58554 */
    short vis_mask;              /* 0x58556 */
    short best_dist;             /* 0x58558 */
};
extern struct TargetSearch target_search;      /* 0x58540 */

extern unsigned short fn_13348(short x, short y, unsigned mask);   /* 0x13348 */
extern unsigned fn_13270(Point *p, Unit *u);   /* 0x13270 distance point->unit */

/* @0x10834 */
void UnitConsiderTarget(Unit *u)
{
    unsigned f = u->flags.w & 0x207;
    unsigned mask;
    unsigned dist;
    unsigned score;

    if (f != 0)
        return;
    mask = u->flags2 & target_search.vis_mask;
    if (mask != 0)
        return;
    if (target_search.enemy_map[u->owner] == 0)
        return;
    if (u->timer36 != 0)
        return;
    dist = fn_13270(&target_search.origin, u);
    score = target_priority[u->type];
    if (dist < target_search.min_range)
        return;
    if (dist > target_search.range) {
        if (target_search.chase != 0)
            return;
        if (dist > target_search.best_dist)
            return;
    }
    score -= dist * dist;
    if ((short) score < 0)
        score = 1;
    if (target_search.flag_4e == 0 && u->timer38 != 0)
        score = 0;
    if ((short) score <= target_search.best_score)
        return;
    target_search.best = u;
    target_search.best_dist = dist;
    target_search.best_score = score;
}
