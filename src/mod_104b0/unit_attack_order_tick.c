/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_110a0 (0x110a0..0x11530), the attack order handlers, "OPT" style.
 * UnitAttackOrderTick (0x1143c): the shared body of the human attack order
 * (order 6) and the AI attack order (order 8); flag selects the callback and
 * the crowding check.  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c */
extern int fn_2eefc(Unit *u, void (*cb)(Unit *), int flag);   /* 0x2eefc */
extern void UnitCallForHelp(Unit *u);                         /* 0x10b1c */
extern int UnitCheckAttackCrowding(Unit *u);                  /* 0x11140 */
extern int fn_222d8(Unit *u);                                 /* 0x222d8 */
extern int UnitWanderStep(Unit *u);                           /* 0x11298 */
extern void UnitSetNextOrder(Unit *u, unsigned char order);   /* 0x2eeac */
extern int UnitAttackStrike(Unit *u);                         /* 0x110a4 */
extern unsigned char fn_1def0(Unit *u);                       /* 0x1def0 */
extern void fn_1bb90(Unit *u);                                /* 0x1bb90 */

/* @0x1143c */
int UnitAttackOrderTick(Unit *u, void (*cb)(Unit *), int flag)
{
    if (fn_2eefc(u, cb, flag) != 0)
        return 1;
    if (dat_5008c[u->owner] == 0 && u->target == u->attacker)
        UnitCallForHelp(u);
    if (u->type >= 4 && u->type <= 5) {
        if (UnitCheckAttackCrowding(u) != 0)
            return 1;
    }
    if (fn_222d8(u) != 0) {
        if (UnitAttackStrike(u) != 0) {
            u->facing = fn_1def0(u);
            fn_1bb90(u);
        }
    } else if (u->attacker != 0) {
        if (UnitWanderStep(u) != 0)
            return 1;
        UnitSetNextOrder(u, 2);
    } else {
        UnitSetNextOrder(u, 2);
    }
    return 1;
}
