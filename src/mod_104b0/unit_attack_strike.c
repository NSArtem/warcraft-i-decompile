/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_110a0 (0x110a0..0x11530), the attack order handlers, "OPT" style.
 * UnitAttackStrike (0x110a4): "strike now if the energy allows it".  For the
 * missile types 0xa..0xe the energy byte (+0x1a) must be below 1 (or 5 for a
 * non-player owner); then the unit either closes on its last attacker or
 * stops.  Returns 1 when there is nothing to do.  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c */
extern void UnitApproachPoint(Unit *u, Unit *enemy, Point *out); /* 0x107a0 */
extern void UnitOrderTarget(Unit *u, short x, short y, Unit *target, void (*fn)(Unit *)); /* 0x2e100 */
extern void UnitSetNextOrder(Unit *u, unsigned char order);   /* 0x2eeac */
extern void fn_20eb4(Unit *u);                                /* 0x20eb4 */

/* @0x110a4 */
int UnitAttackStrike(Unit *u)
{
    unsigned cost;

    if (u->type < 0xa || u->type > 0xe)
        return 1;
    cost = (dat_5008c[u->owner] != 0) ? 1 : 5;
    if (u->energy >= cost)
        return 1;
    if (u->attacker == 0) {
        UnitSetNextOrder(u, 2);
    } else {
        Point p;

        UnitApproachPoint(u, u->attacker, &p);
        UnitOrderTarget(u, p.x, p.y, 0, fn_20eb4);
        u->attacker = 0;
    }
    return 0;
}
