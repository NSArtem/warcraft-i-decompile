/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitAcquireTarget (0x10908): the target scan.  Initialises the per-call
 * search state (target_search), scores the current target and last attacker,
 * scans a box of the object map around the unit and, when a better enemy is
 * found, orders the unit to attack it.  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c */
extern unsigned char unit_sight_range[];       /* 0x51c6c */
extern unsigned char projectile_params[];      /* 0x511e0 */
extern unsigned short player_visibility_mask[];/* 0x51de6 */
extern unsigned char hostility[];              /* 0x51883 */
extern Unit **object_map;                      /* 0x58580 */

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

extern void fn_2207c(Unit *u);                                 /* 0x2207c */
extern void UnitConsiderTarget(Unit *u);                       /* 0x10834 */
extern void UnitOrderTarget(Unit *u, short x, short y, Unit *target, void (*fn)(Unit *)); /* 0x2e100 */

/* @0x10908 */
int UnitAcquireTarget(Unit *u, int chase, void (*cb)(Unit *))
{
    unsigned type = u->type;
    unsigned r;
    unsigned w;
    int x0, y0, h;
    unsigned row;

    target_search.origin = *(Point *) &u->tx;
    target_search.best = 0;
    target_search.best_score = -1;
    target_search.best_dist = -1;
    target_search.range = unit_sight_range[type];
    target_search.chase = chase;
    target_search.enemy_map = hostility + u->owner * 5;
    target_search.vis_mask = player_visibility_mask[u->owner];
    target_search.flag_4e = (dat_5008c[u->owner] == 0);
    if (type == 4 || type == 5)
        target_search.min_range = projectile_params[1];
    else
        target_search.min_range = 0;
    fn_2207c(u);
    if (u->target != 0)
        UnitConsiderTarget(u->target);
    if (u->attacker != 0)
        UnitConsiderTarget(u->attacker);
    r = unit_sight_range[type];
    w = r * 2 + 1;
    if (target_search.best == 0 || target_search.best_dist > target_search.range) {
        if (target_search.flag_4e) {
            r++;
            w += 2;
        } else {
            r += 2;
            w += 4;
        }
    }
    x0 = u->tx - r;
    y0 = u->ty - r;
    h = w;
    if (x0 < 0) {
        w += x0;
        x0 = 0;
    } else if (x0 + w >= 0x40) {
        w = 0x40 - x0;
    }
    if (y0 < 0) {
        h += y0;
        y0 = 0;
    } else if (y0 + h >= 0x40) {
        h = 0x40 - y0;
    }
    {
        Unit **p = object_map + y0 * 0x40 + x0;

        for (row = 0; row < h; row++) {
            unsigned col;

            for (col = 0; col < w; col++) {
                Unit *c = *p++;
                if (c != 0)
                    UnitConsiderTarget(c);
            }
            p += 0x40 - w;
        }
    }
    if (target_search.best != 0) {
        Unit *best = target_search.best;

        if (best->type >= 0x20 && best->type <= 0x32 && u->attacker != 0)
            best = target_search.best = u->attacker;
        if (u->target != best) {
            UnitOrderTarget(u, 0, 0, best, cb);
            if ((u->f12 & 8) != 0) {
                u->f12 = 4;
                u->f13 = 0;
            }
            return 1;
        }
    }
    return 0;
}
