/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitCalcDamage (0x104b0): the damage a unit's attack does, from the
 * per-type damage tables plus the owner's weapon upgrade, minus the target's
 * armour and armour upgrade, with the 40% "miss" roll.  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern CheatFlags cheat_flags;                 /* 0x51214 */
extern unsigned char dat_5008c[];              /* 0x5008c player type by owner */
extern unsigned char dat_50008[];              /* 0x50008 upgrade row 0 (ranged weapon) */
extern unsigned char dat_5000d[];              /* 0x5000d upgrade row 1 (melee weapon) */
extern unsigned char dat_50035[];              /* 0x50035 upgrade row 9 (armour) */
extern unsigned char unit_damage[];            /* 0x51d5c */
extern unsigned char unit_damage_bonus[];      /* 0x51d7c */
extern unsigned char unit_armour[];            /* 0x51c8c */
extern unsigned char weapon_upgrade_bonus[];   /* 0x51098 */
extern unsigned char armour_upgrade_bonus[];   /* 0x5109b */

extern unsigned short fn_13348(short x, short y, unsigned mask);   /* 0x13348 */
extern int GameRandom(unsigned id);                                 /* 0x19478 LCG */

/* @0x104b0 */
unsigned char UnitCalcDamage(Unit *u)
{
    unsigned dmg;
    unsigned bonus;
    unsigned t;

    if (cheat_flags.f.dev) {
        if (dat_5008c[u->owner] != 0)
            return 0;
        return 0xc8;
    }
    t = u->type;
    dmg = unit_damage[t];
    bonus = unit_damage_bonus[t];
    if (t == 8 || t == 9)
        bonus += weapon_upgrade_bonus[dat_50008[u->owner] & 0xf];
    else
        dmg += weapon_upgrade_bonus[dat_5000d[u->owner] & 0xf];
    if (u->target == 0) {
        if (fn_13348(u->dest_x, u->dest_y, 0xc) == 0)
            return 0;
    } else {
        Unit *v;

        if (GameRandom(0xc) >= 0x6666)
            return 0;
        v = u->target;
        dmg -= unit_armour[v->type];
        dmg -= armour_upgrade_bonus[dat_50035[v->owner] & 0xf];
        if ((short) dmg < 0)
            dmg = 0;
    }
    dmg += bonus;
    if ((short) dmg > 0xff)
        dmg = 0xff;
    return dmg;
}
