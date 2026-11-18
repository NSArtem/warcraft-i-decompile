/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitCallForHelp (0x10b1c): a unit that has just been attacked orders the
 * idle friendly units in the 3x3 tiles around it to attack its attacker.
 * See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char hostility[];              /* 0x51883 */
extern Unit **object_map;                      /* 0x58580 */

extern void UnitOrderTarget(Unit *u, short x, short y, Unit *target, void (*fn)(Unit *)); /* 0x2e100 */
extern void fn_20fac(Unit *u);                 /* 0x20fac AI attack order callback */

/* @0x10b1c */
void UnitCallForHelp(Unit *u)
{
    Unit *attacker = u->attacker;
    unsigned r;
    int x0, y0, w, h;
    unsigned row;

    if (attacker == 0)
        return;
    if (hostility[u->owner * 5 + attacker->owner] == 0)
        return;
    x0 = u->tx - 1;
    y0 = u->ty - 1;
    w = 3;
    h = 3;
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
                if ((c->flags.w & 0x207) != 0)
                    continue;
                if (c->type == 2 || c->type == 3)
                    continue;
                if (c->type >= 0x20 && c->type <= 0x32)
                    continue;
                if (hostility[u->owner * 5 + c->owner] != 0)
                    continue;
                if (c->attacker != 0)
                    continue;
                if (c->order != 2 || c->order_next != 0x1f || c->order_next2 != 0x1f)
                    continue;
                c->attacker = attacker;
                UnitOrderTarget(c, 0, 0, attacker, fn_20fac);
            }
            p += 0x40 - w;
        }
    }
}
