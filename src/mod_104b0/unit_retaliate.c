/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitRetaliate (0x10d34): turns the unit's last attacker (+0x3a) into an
 * order - a direct attack for the melee/siege types, an approach point for
 * the missile types and the workers, and a call for help for the AI.  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c */
extern void UnitApproachPoint(Unit *u, Unit *enemy, Point *out); /* 0x107a0 */
extern void UnitOrderTarget(Unit *u, short x, short y, Unit *target, void (*fn)(Unit *)); /* 0x2e100 */
extern void UnitCallForHelp(Unit *u);                         /* 0x10b1c */
extern int AiWorkerTick(Unit *u);                             /* 0x2b064, mod_295d0.toml */
extern void fn_1bd04(Unit *u);                                /* 0x1bd04 */
extern void fn_20eb4(Unit *u);                                /* 0x20eb4 */
extern void fn_20f30(Unit *u);                                /* 0x20f30 */
extern void fn_20fac(Unit *u);                                /* 0x20fac */

/* @0x10d34 */
int UnitRetaliate(Unit *u, int is_human)
{
    Unit *attacker = u->attacker;
    unsigned type;
    int human;

    if (attacker == 0)
        return 0;
    if ((attacker->flags.w & 0x207) != 0) {
        u->attacker = 0;
        return 0;
    }
    if (dat_5008c[u->owner] == 2) {
        u->attacker = 0;
        return 0;
    }
    human = (dat_5008c[u->owner] == 1);
    type = u->type;
    if (type >= 0x20 && type <= 0x32) {
        u->attacker = 0;
        if (!human)
            fn_1bd04(u);
        return 0;
    }
    if (type >= 0x10 && type <= 0x12) {
        if (type == 0x10)
            return 0;
        {
            Point p;

            UnitApproachPoint(u, attacker, &p);
            UnitOrderTarget(u, p.x, p.y, 0, fn_20eb4);
        }
        u->attacker = 0;
        return 1;
    }
    if (type >= 2 && type <= 3) {
        if (!human || AiWorkerTick(u) == 0) {
            Point p;

            UnitApproachPoint(u, attacker, &p);
            UnitOrderTarget(u, p.x, p.y, 0, fn_20eb4);
        }
        u->attacker = 0;
        if (!human)
            fn_1bd04(u);
        return 1;
    }
    if (u->target == attacker)
        return 0;
    UnitOrderTarget(u, 0, 0, attacker, human ? fn_20f30 : fn_20fac);
    if (!human) {
        UnitCallForHelp(u);
        fn_1bd04(u);
    }
    return 1;
}
