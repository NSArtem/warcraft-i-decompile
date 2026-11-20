/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern short UnitRetaliate(OrderUnit *u);
extern short fn_2eefc(OrderUnit *u, void (*cb)(OrderUnit *), int flag);
extern void fn_210dc(OrderUnit *u);
extern void fn_1cd50(OrderUnit *u);
extern unsigned char fn_1def0(OrderUnit *u);
extern void UnitSetNextOrder(void *u, unsigned char order);
extern void fn_19f70(const char *msg, unsigned code);
extern long dat_50060[5];
extern long dat_50074[5];
extern unsigned short unit_max_hp[0x36];
extern char dat_56ab8[];
extern char dat_56ad8[];

/* @0x141e0 */
int OrderUpdateRepair(OrderUnit *u)
{
    OrderUnit *d = *(OrderUnit **)((char *)u + 0x52);
    unsigned short hp;
    unsigned short cnt;

    if (UnitRetaliate(u) != 0) {
        return 1;
    }
    if (fn_2eefc(u, fn_210dc, 1) != 0) {
        return 1;
    }
    if ((d->flags & 0x80) != 0 || *((unsigned char *)d + 0x4e) != 0) {
        if (d->hp == unit_max_hp[d->type]) {
            UnitSetNextOrder(u, 2);
            return 1;
        }
        if (dat_50060[u->owner] >= 1 && dat_50074[u->owner] >= 1) {
            u->facing = fn_1def0(u);
            hp = (unsigned short)(d->hp + 8);
            d->hp = hp;
            if (hp > unit_max_hp[d->type]) {
                d->hp = unit_max_hp[d->type];
            }
            cnt = (unsigned short)(*(unsigned short *)((char *)d + 0x52) + 1);
            *(unsigned short *)((char *)d + 0x52) = cnt;
            if ((*(long *)((char *)d + 0x50) >> 16) >= 1) {
                *(unsigned short *)((char *)d + 0x52) = (unsigned short)(cnt - 1);
                dat_50060[u->owner]--;
                dat_50074[u->owner]--;
            }
            return 1;
        }
        if (u->owner == 0) {
            if (dat_50060[u->owner] < 1) {
                fn_19f70(dat_56ab8, 0x24);
            } else {
                fn_19f70(dat_56ad8, 0x24);
            }
        }
        UnitSetNextOrder(u, 2);
        return 1;
    } else {
        fn_1cd50(u);
    }
    return 1;
}
