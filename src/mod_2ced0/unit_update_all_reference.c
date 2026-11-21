/* codegen-compiler: 10.0a */
#include "mod_2ced0_c.h"

extern Unit *unit_array;
extern unsigned short unit_max_hp[0x36];
extern union { unsigned long w; unsigned char b[4]; } cheat_flags;
extern void *dat_5a7b4;
extern void *dat_5a7b8;
extern void UnitUpdateDamageFrame(void *u);
extern void UnitStartDeath(Unit *u);

/* @0x2d204 */
void UnitUpdateAll(void)
{
    Unit *p = unit_array;
    short i = 200;
    int mx;
    int half;
    unsigned hp;

    while (--i != -1) {
        if ((p->flags & 0x207) == 0 && p->b1b >= 0x20) {
            mx = unit_max_hp[p->b1b];
            half = mx / 2;
            hp = p->hp;
            if ((int)hp < half) {
                p->ptr58 = dat_5a7b4;
            } else if ((int)hp < (mx * 3) / 4) {
                p->ptr58 = dat_5a7b8;
            } else {
                p->ptr58 = 0;
            }
            if ((p->flags & 0x80) == 0 && p->b4e != 0) {
                if ((cheat_flags.b[0] & 2) || --p->timer == 0) {
                    UnitStartDeath(p);
                    UnitUpdateDamageFrame(p);
                }
            }
        }
        p++;
    }
}
