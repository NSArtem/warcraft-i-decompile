/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_110a0 (0x110a0..0x11530), the attack order handlers, "OPT" style.
 * AttackOrderAtPoint (0x11344), order 7: retaliate first, then move to the
 * destination and strike when it is reached; a destination that is not a
 * feature tile stops the unit.  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern int UnitRetaliate(Unit *u, int is_human);              /* 0x10d34 */
extern int fn_222d8(Unit *u);                                 /* 0x222d8 */
extern void UnitOrderTarget(Unit *u, short x, short y, Unit *target, void (*fn)(Unit *)); /* 0x2e100 */
extern void fn_20f44(Unit *u);                                /* 0x20f44 */
extern unsigned short fn_13348(short x, short y, unsigned mask); /* 0x13348 */
extern void UnitSetNextOrder(Unit *u, unsigned char order);   /* 0x2eeac */
extern int UnitAttackStrike(Unit *u);                         /* 0x110a4 */
extern unsigned char fn_1de60(Point from, Point to);          /* 0x1de60 */
extern void fn_1bb90(Unit *u);                                /* 0x1bb90 */

/* @0x11344 */
int AttackOrderAtPoint(Unit *u)
{
    if (UnitRetaliate(u, 0) != 0)
        return 1;
    if (fn_222d8(u) == 0) {
        UnitOrderTarget(u, u->dest_x, u->dest_y, u->target, fn_20f44);
        return 1;
    }
    if (fn_13348(u->dest_x, u->dest_y, 0xc) == 0) {
        UnitSetNextOrder(u, 2);
        return 1;
    }
    if (UnitAttackStrike(u) != 0) {
        u->facing = fn_1de60(*(Point *) &u->tx, *(Point *) &u->dest_x);
        fn_1bb90(u);
    }
    return 1;
}
