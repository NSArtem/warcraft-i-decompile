/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_110a0 (0x110a0..0x11530), the attack order handlers, "OPT" style.
 * AttackOrderTarget (0x113e0), order 5: the target attack.  Validates the
 * target, calls for help, and strikes with the target facing.  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c */
extern int fn_2eefc(Unit *u, void (*cb)(Unit *), int flag);   /* 0x2eefc */
extern void fn_20f84(Unit *u);                                /* 0x20f84 */
extern void UnitCallForHelp(Unit *u);                         /* 0x10b1c */
extern int UnitAttackStrike(Unit *u);                         /* 0x110a4 */
extern unsigned char fn_1def0(Unit *u);                       /* 0x1def0 */
extern void fn_1bb90(Unit *u);                                /* 0x1bb90 */

/* @0x113e0 */
int AttackOrderTarget(Unit *u)
{
    if (fn_2eefc(u, fn_20f84, 1) != 0)
        return 1;
    if (dat_5008c[u->owner] == 0 && u->target == u->attacker)
        UnitCallForHelp(u);
    if (UnitAttackStrike(u) != 0) {
        u->facing = fn_1def0(u);
        fn_1bb90(u);
    }
    return 1;
}
