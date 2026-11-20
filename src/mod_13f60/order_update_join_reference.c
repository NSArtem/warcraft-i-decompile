/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern short fn_13a90(OrderUnit *u);
extern void fn_13c84(OrderUnit *u);
extern void fn_13c04(OrderUnit *u);
extern void fn_1c9c0(OrderUnit *u);
extern void UnitIdleTurn(OrderUnit *u);
extern void UnitSetNextOrder(void *u, unsigned char order);
extern void __cdecl PaletteCycleEnable(unsigned char id);
extern unsigned char dat_500de;
extern unsigned long ai_wave_timer;
extern unsigned short ai_site_count[5];

/* @0x14084 */
int OrderUpdateJoin(OrderUnit *u)
{
    int i;
    int t;

    if (u->hp > 5 || fn_13a90(u) != 0) {
        t = u->type;
        if (t < 2 || t > 3) {
            for (i = 0; i != 5; i++) {
                ai_site_count[i] = 0xffff;
                ai_wave_timer = 1;
            }
        }
        fn_13c84(u);
        if (u->type == 0x10) {
            u->type = 8;
        }
        u->owner = 0;
        fn_13c04(u);
        PaletteCycleEnable(0);
        dat_500de |= 1;
        UnitSetNextOrder(u, 2);
        fn_1c9c0(u);
        return 1;
    } else {
        t = u->type;
        if (t != 0x10 && t != 0xf) {
            UnitIdleTurn(u);
        }
        return 1;
    }
}
