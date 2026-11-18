/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_110a0 (0x110a0..0x11530), the attack order handlers, "OPT" style.
 * AttackOrderHuman (0x114d8), order 6: the player-issued attack order; the
 * shared body with the human "resume move" callback and the crowding flag on.
 * See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern int UnitAttackOrderTick(Unit *u, void (*cb)(Unit *), int flag); /* 0x1143c */
extern void fn_20f30(Unit *u);                                /* 0x20f30 */

/* @0x114d8 */
int AttackOrderHuman(Unit *u)
{
    return UnitAttackOrderTick(u, fn_20f30, 1);
}
