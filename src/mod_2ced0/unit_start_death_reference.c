/* codegen-compiler: 10.0a */
#include "mod_2ced0_c3.h"

/* @0x2d0e0 */
void UnitStartDeath(Unit *u)
{
    short i;
    char *p;

    u->s4c = 10;
    u->s52++;
    SndConstructionTick(u);
    if (u->s52 >= u->s50) {
        u->b1a = 0xff;
        if (u->s52 == u->s50)
            return;
        u->b1c = u->type;
        u->b7 = 0;
        UnitStartAnim(u, 2);
        u->b1a++;
        UnitCountRemove(u);
        u->flags |= 0x80;
        UnitCountAdd(u);
        status_dirty = 1;
        player_stat_50d98[u->owner]--;
        UnitUpdateGraphicsIndex(u);
        SndWorkComplete(u);
        p = (char *)unit_array;
        i = 200;
        while (--i != -1) {
            Unit *q = (Unit *)p;
            if ((q->flags & 0x207) == 0 && (q->flags & 8) != 0 && *(Unit **)((char *)q + 0x52) == u) {
                HarvestDepositCargo(q);
                *((unsigned char *)u + 0x4e) = (unsigned char)(*((unsigned char *)u + 0x4e) - 1);
                fn_2e5c8(q, &unit_type_size[u->type][0]);
                return;
            }
            p += 0x5c;
        }
    } else {
        u->b1a = (unsigned char)(((*(long *)((char *)u + 0x50) >> 16) * 255) /
                                 (*(long *)((char *)u + 0x4e) >> 16));
    }
}
