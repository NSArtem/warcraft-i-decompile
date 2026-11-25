/* codegen-compiler: 10.0a */
#include "mod_2ced0_c7.h"

extern void *unit_array;
extern void *object_array;
extern struct Unit * volatile dat_50f7c;
extern unsigned char dat_50012[5];
extern unsigned char dat_5a7c6;
extern unsigned char dat_5a7c7;
extern void (*dat_511f4[])(void *);
extern int (*order_update_table[0x20])(void *);
extern short fn_10473(void *record);
extern void fn_2ea4c(struct Unit *u);
extern unsigned short UnitAdvanceOrder(struct Unit *u, int use_arg);
extern void UnitUpdateAll(void);
extern void UpdateUnitTimersAndResources(void);
extern void DrawListSort(void);

void SimulationTick(void)
{
    struct Unit *u;
    unsigned char *object;
    unsigned char *object_arg;
    short units_left;
    short objects_left;
    short clear_mask;
    unsigned short flags;
    unsigned short timer;
    unsigned short decremented;
    unsigned char object_flags;
    unsigned short zero;

    dat_50f7c = unit_array;
    units_left = 200;
    clear_mask = (short)~0x1800;
    zero = 0;
    goto test_units;

check_unit:
    u = dat_50f7c;
    flags = *(volatile unsigned short *)&u->flags;
    flags &= 1;
    if (((unsigned)flags & 0xffffU) != 0)
        goto next_unit;
    flags = *(volatile unsigned short *)&u->flags;
    flags &= 0x0200;
    if (((unsigned)flags & 0xffffU) != 0) {
        timer = u->gone_timer;
        if (zero == timer)
            goto next_unit;
        decremented = (unsigned short)(timer - 1);
        u->gone_timer = decremented;
        goto next_unit;
    }
    timer = u->tick_timer;
    if (zero != timer) {
        decremented = (unsigned short)(timer - 1);
        u->tick_timer = decremented;
    }
    u = dat_50f7c;
    flags = *(volatile unsigned short *)&u->flags;
    flags &= 0x1000;
    if (((unsigned)flags & 0xffffU) != 0) {
        flags = *(volatile unsigned short *)&u->flags;
        flags &= 0x0800;
        if (((unsigned)flags & 0xffffU) == 0)
            goto next_unit;
        u->flags &= (unsigned short)clear_mask;
    } else {
        dat_5a7c6 = dat_50012[u->owner] & 0x0f;
        dat_5a7c7 = u->tick_bits & 0x20;
        if (fn_10473(u) == 0)
            goto next_unit;
        fn_2ea4c(dat_50f7c);
    }
    u = dat_50f7c;
    flags = *(volatile unsigned short *)&u->flags;
    flags &= 0x0800;
    if (((unsigned)flags & 0xffffU) != 0) {
        u->flags &= (unsigned short)clear_mask;
        ((volatile unsigned char *)&u->flags)[1] |= 0x10;
        goto next_unit;
    }
    if (UnitAdvanceOrder(u, zero) != 0)
        goto next_unit;
    u = dat_50f7c;
    if ((short)order_update_table[u->order](u) != 0)
        UnitAdvanceOrder(dat_50f7c, zero);

next_unit:
    ++dat_50f7c;
test_units:
    if (--units_left != -1)
        goto check_unit;

    dat_50f7c = 0;
    object = object_array;
    objects_left = 100;
    object_arg = object + 6;
    goto test_objects;

check_object:
    object_flags = *(volatile unsigned char *)(object + 1);
    object_flags &= 1;
    if (((unsigned)object_flags & 0xffU) != 0)
        goto next_object;
    if (fn_10473(object_arg) == 0)
        goto next_object;
    dat_511f4[object[2]](object);
next_object:
    object_arg += 0x26;
    object += 0x26;
test_objects:
    if (--objects_left != -1)
        goto check_object;
    UnitUpdateAll();
    UpdateUnitTimersAndResources();
    DrawListSort();
}
