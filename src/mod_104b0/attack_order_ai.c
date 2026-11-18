/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_110a0 (0x110a0..0x11530), the attack order handlers, "OPT" style.
 * AttackOrderAI (0x114ec), order 8: the AI attack order; the crowding flag is
 * "small unit" (the missile types 0xa..0xe never, the rest when the sight
 * radius is <= 1).  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char unit_sight_range[];       /* 0x51c6c */
extern int UnitAttackOrderTick(Unit *u, void (*cb)(Unit *), int flag); /* 0x1143c */
extern void fn_20fac(Unit *u);                                /* 0x20fac */

/* @0x114ec */
int AttackOrderAI(Unit *u)
{
    int e;
    int type = u->type;

    if (type >= 0xa && type <= 0xe) {
        e = 0;
    } else {
        e = unit_sight_range[type];
        e = (e <= 1);
    }
    return UnitAttackOrderTick(u, fn_20fac, e);
}
