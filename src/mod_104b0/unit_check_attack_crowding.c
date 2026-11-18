/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_110a0 (0x110a0..0x11530), the attack order handlers, "OPT" style.
 * UnitCheckAttackCrowding (0x11140): the siege units (types 4/5) give up the
 * order when they are too close to the target or when enough friendly units
 * already stand around it.  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c */
extern unsigned char hostility[];              /* 0x51883 */
extern unsigned char projectile_params[];      /* 0x511e0 */
extern Unit **object_map;                      /* 0x58580 */

extern unsigned fn_13270(Point *p, Unit *u);                  /* 0x13270 */
extern void UnitSetNextOrder(Unit *u, unsigned char order);   /* 0x2eeac */

/* @0x11140 */
int UnitCheckAttackCrowding(Unit *u)
{
    Unit *t = u->target;
    int n;
    int x0, y0, w, h;
    unsigned row;

    if (fn_13270((Point *) &u->tx, t) < projectile_params[1]) {
        UnitSetNextOrder(u, 2);
        return 1;
    }
    n = (dat_5008c[u->owner] != 0) ? 2 : 0;
    x0 = t->tx - 2;
    y0 = t->ty - 2;
    w = 5;
    h = 5;
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

        for (row = 0; row < (unsigned) h; row++) {
            int col;

            for (col = 0; col < w; col++) {
                Unit *c = *p++;

                if (c == 0)
                    continue;
                if (hostility[u->owner * 5 + c->owner] != 0)
                    continue;
                if (--n < 0) {
                    UnitSetNextOrder(u, 2);
                    return 1;
                }
            }
            p += 0x40 - w;
        }
    }
    return 0;
}
