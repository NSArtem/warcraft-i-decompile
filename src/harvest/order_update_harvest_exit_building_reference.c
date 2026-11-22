/* codegen-compiler: 10.0a */
#include "harvest.h"

extern int AiWorkerTick(Unit *u);
extern void UnitOrderTarget(Unit *u, int x, int y, Unit *target, void (*fn)(Unit *));
extern int fn_2e5c8(Unit *u, short *size);

int OrderUpdateHarvestExitBuilding(Unit *u)
{
    unsigned char type;
    unsigned int owner;
    int result;
    long x_view;
    int y;
    Unit *target;
    void (*callback)(Unit *);

    if (u->harvest_flags & 4)
        type = 0x30;
    else
        type = 0x28;
    u->harvest_flags &= 0xfb;
    result = fn_2e5c8(u, unit_type_size[type]);
    if ((short)result == 0)
        return result;

    if (u->harvest_flags & 0x20) {
        callback = UiOrderSetNext3_11;
        owner = u->owner;
        target = player_town_hall[owner];
        y = *(long *)&player_home_point[owner] >> 16;
        x_view = *(long *)((char *)&player_home_point_preceding_word + owner * 4);
    } else {
        if (player_controller_type[u->owner] == 1 && (short)AiWorkerTick(u) != 0)
            goto success;
        if (!(u->harvest_flags & 8))
            goto success;
        u->harvest_flags &= 0xf7;
        callback = fn_21094;
        target = u->saved_target;
        y = u->saved_point.packed >> 16;
        x_view = *(long *)((char *)&u->saved_point - 2);
    }
    UnitOrderTarget(u, x_view >> 16, y, target, callback);
success:
    return 1;
}
