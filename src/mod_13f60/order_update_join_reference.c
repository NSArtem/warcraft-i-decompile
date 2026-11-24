/* codegen-compiler: 10.0a */
#include "mod_13f60.h"
#include "mod_13b30_f1.h"

extern int HasJoinCandidateNearby(struct Unit *u);
extern void UnitUpdateGraphicsIndex(struct Unit *u);
extern void UnitIdleTurn(OrderUnit *u);
extern void UnitSetNextOrder(void *u, unsigned char order);
extern void __cdecl PaletteCycleEnable(unsigned char id);
extern unsigned short scenario_palette_cycle_enable_mask;
extern unsigned long ai_wave_timer;
extern unsigned short ai_site_count[5];

/* @0x14084 */
int OrderUpdateJoin(OrderUnit *u)
{
    int i;
    int t;

    if (u->hp > 5 || (short)HasJoinCandidateNearby((struct Unit *)u) != 0) {
        t = u->type;
        if (t < 2 || t > 3) {
            for (i = 0; i != 5; i++) {
                ai_site_count[i] = 0xffff;
                ai_wave_timer = 1;
            }
        }
        UnitCountRemove((struct Unit *)u);
        if (u->type == 0x10) {
            u->type = 8;
        }
        u->owner = 0;
        UnitCountAdd((struct Unit *)u);
        PaletteCycleEnable(0);
        *(unsigned char *)&scenario_palette_cycle_enable_mask |= 1;
        UnitSetNextOrder(u, 2);
        UnitUpdateGraphicsIndex((struct Unit *)u);
        return 1;
    } else {
        t = u->type;
        if (t != 0x10 && t != 0xf) {
            UnitIdleTurn(u);
        }
        return 1;
    }
}
