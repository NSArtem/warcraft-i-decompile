/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern void fn_11ec0(OrderUnit *u, int n);
extern void fn_1c9c0(OrderUnit *u);
extern void fn_26360(OrderUnit *u, unsigned sound);
extern void fn_13860(OrderUnit *u);
extern void TerrainStartRegionA(OrderUnit *u);

/* @0x13f68 */
int OrderUpdateDeath(OrderUnit *u)
{
    int t = u->type;
    unsigned char s;

    if (t != 0x33) {
        if (t < 0x20) {
            if (t == 0x17) {
                fn_11ec0(u, 7);
            }
            s = death_sound_by_type[u->type];
            if (s != 0) {
                u->owner = 4;
                u->type = 0x33;
                fn_1c9c0(u);
                u->frame = 0;
                u->flags |= 2;
                fn_26360(u, s);
                return 0;
            }
        } else {
            fn_13860(u);
            TerrainStartRegionA(u);
        }
    }
    u->flags &= 0xfff9;
    UnitSetOrder(u, 0);
    u->flags |= 4;
    return 0;
}
