/* codegen-compiler: 10.0a */
#include "harvest.h"

extern void fn_13954(Unit *u);
extern void UnitUpdateGraphicsIndex(Unit *u);
extern void fn_2207c(Unit *u);
extern void SelectionRemoveUnit(Unit *u);
extern void fn_2e384(Unit *u);
extern void fn_2e9c4(short x, short y, unsigned char owner);
extern void UnitSetOrder(Unit *u, unsigned char order);
extern void UnitSetNextOrder(void *u, unsigned char order);

int OrderUpdateHarvestEnterBuilding(Unit *u)
{
    Unit *tile_unit;
    Unit *building;
    long row;
    unsigned char flags;
    unsigned char count;
    unsigned long remaining;
    unsigned long capped;
    unsigned long amount;
    unsigned long left;

    fn_2207c(u);
    if (u->work.target == 0) {
        UnitSetOrder(u, 2);
        goto done;
    }
    if (u->harvest_flags & 0x10)
        goto enter;

    row = (u->position.packed >> 16) * 64;
    tile_unit = object_map[(*(long *)((char *)&u->position - 2) >> 16) + row];
    if (u != tile_unit)
        goto enter;
    fn_13954(tile_unit);
    flags = tile_unit->harvest_flags;
    u->harvest_flags = (unsigned char)(flags | 0x10);
    u->position.xy[0] += (short)dir_dx[u->direction];
    u->position.xy[1] += (short)dir_dy[u->direction];
    return 0;

enter:
    u->state_flags |= 8;
    SelectionRemoveUnit(u);
    u->position.packed = u->work.target->position.packed;
    u->position_prefix = u->work.target->position_prefix;
    fn_2e9c4((short)(u->position.xy[0] + 1), (short)(u->position.xy[1] + 1), u->owner);
    UnitSetOrder(u, 0x0d);
    u->entry_timer = 0x50;

    building = u->work.target;
    if (!(building->state_flags & 0x80)) {
        count = ((unsigned char *)&building->target_point)[0];
        if (count != 0)
            goto done;
        ((unsigned char *)&building->target_point)[0] = (unsigned char)(count + 1);
        UnitSetNextOrder(u, 9);
        return 0;
    }

    if ((short)HarvestDepositCargo(u) != 0)
        goto done;
    remaining = u->work.target->work.deposit.remaining;
    if (remaining <= 0UL)
        goto done;
    if (remaining < 100UL)
        capped = remaining;
    else
        capped = 100UL;
    amount = capped;
    u->harvest_flags |= 0x20;
    UnitUpdateGraphicsIndex(u);
    if (player_controller_type[u->owner] == 1 &&
        (u->work.target->building_flags & 0x100) != 0) {
        if (capped > 5UL)
            capped = 5UL;
        amount = capped;
    }

    building = u->work.target;
    left = building->work.deposit.remaining;
    left -= amount;
    building->work.deposit.remaining = left;
    if (left == 0) {
        fn_2e384(u->work.target);
        u->harvest_flags &= 0xf7;
        return 0;
    }
    u->saved_point.packed = u->target_point.packed;
    u->saved_target = u->work.target;
    u->harvest_flags |= 8;
done:
    return 0;
}
