/* codegen-compiler: 10.0a */
#include "harvest.h"

extern int UnitRetaliate(Unit *u, int is_human);
extern void UnitSetWorkSound(Unit *u);
extern void UnitUpdateGraphicsIndex(Unit *u);
extern unsigned char fn_1de60(long from, long to);
extern int fn_222d8(Unit *u);
extern void UnitStartAnim(Unit *u, unsigned sound);
extern void TerrainStartRegionB(Unit *u);
extern int TerrainTileIsClear(short *pt);
extern int TerrainFindClearTile(unsigned short *p);
extern void UnitOrderTarget(Unit *u, int x, int y, Unit *target, void (*fn)(Unit *));
extern void UnitSetNextOrder(void *u, unsigned char order);

#pragma aux OrderUpdateHarvest modify exact [eax gs]

int OrderUpdateHarvest(Unit *u, int is_human)
{
    Unit *mine;
    Unit *hall;
    HarvestPointView tile;
    unsigned char ticks;

    if ((short)UnitRetaliate(u, is_human) != 0)
        goto done;

    if (u->harvest_flags & 0x80) {
        mine = u->work.target;
        if (mine != 0 && (mine->state_flags & 0x207) == 0)
            goto approach;
idle:
        UnitSetNextOrder(u, 2);
        goto done;
approach:
        if ((short)fn_222d8(u) != 0) {
            HarvestQueueBuildingEntry(u);
            goto done;
        }
        UnitOrderTarget(u, 0, 0, u->work.target, fn_21094);
        goto done;
    }

    if (!(u->harvest_flags & 0x40)) {
        FatalError(harvest_invalid_state_msg);
        goto done;
    }
    if ((short)fn_222d8(u) == 0) {
        UnitOrderTarget(u, *(long *)((char *)&u->target_point - 2) >> 16,
                        u->target_point.packed >> 16, u->work.target, fn_21094);
        return 1;
    }
    if ((short)TerrainTileIsClear(u->target_point.xy) != 0) {
        ticks = u->work_ticks;
        if (ticks < 0x32) {
            if (ticks == 0)
                u->direction = fn_1de60(u->position.packed, u->target_point.packed);
            UnitSetWorkSound(u);
        } else {
            UnitStartAnim(u, harvest_sound_ids[0]);
            TerrainStartRegionB(u);
            u->saved_point.packed = u->target_point.packed;
            u->saved_target = u->work.target;
            u->harvest_flags |= 0x28;
            UnitUpdateGraphicsIndex(u);
            hall = player_town_hall[u->owner];
            if (hall != 0) {
                UnitOrderTarget(u, 0, 0, hall, UiOrderSetNext3_11);
                ++u->work_ticks;
                return 1;
            }
            UnitSetNextOrder(u, 2);
        }
        ++u->work_ticks;
        return 1;
    }
    tile.packed = u->position.packed;
    if ((short)TerrainFindClearTile(tile.words) == 0)
        goto idle;
    UnitOrderTarget(u, *(long *)((char *)&tile - 2) >> 16,
                    tile.packed >> 16, 0, fn_21094);
    return 1;

done:
    return 1;
}
