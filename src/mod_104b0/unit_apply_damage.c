/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitApplyDamage (0x10650): subtract the damage from the victim's hit points
 * and, when they run out, award the kill, update the counters, remove the unit
 * and re-target everything that was aiming at it.  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c player type by owner */
extern unsigned short dat_50dac[];             /* 0x50dac killed-men counter */
extern unsigned short dat_50db6[];             /* 0x50db6 killed-buildings counter */

extern void UnitSetLastAttacker(Unit *u, Unit *attacker);     /* 0x10ce0 */
extern void UnitRemove(Unit *u);                              /* 0x2e2a0 */
extern void fn_2207c(Unit *u);                                /* 0x2207c */
extern void ScoreOnMenKilled(unsigned short killer, Unit *victim);      /* 0x25198 */
extern void ScoreOnBuildingKilled(unsigned short killer, Unit *victim); /* 0x2529c */

/* @0x10650  (attacker = eax, victim = edx, damage = bl) */
void UnitApplyDamage(Unit *attacker, Unit *victim, unsigned char damage)
{
    if ((victim->flags.w & 0x207) != 0)
        return;
    UnitSetLastAttacker(victim, attacker);
    if (victim->timer38 != 0)
        return;
    if (damage == 0)
        return;
    if (damage < victim->hp) {
        victim->hp -= damage;
        return;
    }
    if (victim->type < 0x20) {
        ScoreOnMenKilled(attacker->owner, victim);
        dat_50dac[attacker->owner]++;
    } else {
        ScoreOnBuildingKilled(attacker->owner, victim);
        dat_50db6[attacker->owner]++;
    }
    UnitRemove(victim);
    fn_2207c(attacker);
}
