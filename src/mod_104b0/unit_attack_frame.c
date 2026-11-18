/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitAttackFrame (0x106ec): the frame of the attack animation at which the
 * blow lands.  Missile types spawn a projectile (BulletSpawn) and resolve the
 * damage when it hits; the melee types resolve it here against the target unit
 * or, with no target, against the destination tile.  One pointer per player in
 * the table at 0x510b0.  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c */
extern unsigned char unit_projectile[];        /* 0x51d9c */

extern void fn_11a10(Unit *u);                                 /* 0x11a10 BulletSpawn */
extern void fn_11ec0(Unit *u, int sound);                      /* 0x11ec0 */
extern void TileApplyDamage(unsigned short x, unsigned short y, unsigned char d); /* 0x105d0 */
extern unsigned char UnitCalcDamage(Unit *u);                  /* 0x104b0 */
extern void UnitApplyDamage(Unit *attacker, Unit *victim, unsigned char d); /* 0x10650 */

/* @0x106ec */
void UnitAttackFrame(Unit *u)
{
    unsigned t = u->type;

    if (unit_projectile[t] == 0xc) {
        Unit *v;

        if (t == 0x17)
            fn_11ec0(u, 7);
        if (u->target != 0) {
            v = u->target;
            UnitApplyDamage(u, v, UnitCalcDamage(u));
        } else {
            TileApplyDamage(u->dest_x, u->dest_y, UnitCalcDamage(u));
        }
    } else {
        if (t >= 0xa && t <= 0xe) {
            if (dat_5008c[u->owner] != 0)
                u->energy -= 1;
            else
                u->energy -= 5;
        }
        fn_11a10(u);
    }
}
