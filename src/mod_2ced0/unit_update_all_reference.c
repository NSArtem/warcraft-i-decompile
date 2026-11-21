/* codegen-compiler: 10.0a */
#include "mod_2ced0_c.h"

extern Unit *unit_array;
extern unsigned short unit_max_hp[0x36];
extern struct { unsigned long b0 : 1; unsigned long fast_build : 1; } cheat_flags;
extern void *damage_fire_heavy;
extern void *damage_fire_light;
extern void UnitUpdateDamageFrame(void *u);
extern void UnitStartDeath(Unit *u);

/* @0x2d204 */
void UnitUpdateAll(void)
{
    Unit *p = unit_array;
    unsigned short i = 200;
    int mx;
    int half;
    unsigned hp;

    while (i--) {
        if ((p->flags & 0x207) == 0 && p->b1b >= 0x20) {
            mx = unit_max_hp[p->b1b];
            half = mx / 2;
            hp = p->hp;
            if ((int)hp < half) {
                p->ptr58 = damage_fire_heavy;
            } else if ((int)hp < (mx * 3) / 4) {
                p->ptr58 = damage_fire_light;
            } else {
                p->ptr58 = 0;
            }
            if ((p->flags & 0x80) == 0 && p->b4e != 0) {
                if (cheat_flags.fast_build || --p->timer == 0) {
                    UnitStartDeath(p);
                    UnitUpdateDamageFrame(p);
                }
            }
        }
        p++;
    }
}
