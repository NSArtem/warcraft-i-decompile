/* codegen-compiler: 10.0a */
#include "mod_13b30_f1.h"

extern unsigned short player_town_hall_count[5];

/* @0x13b9c */
void CountTownHallDelta(struct Unit *u, short delta)
{
    player_town_hall_count[*((unsigned char *)u + 0x1e)] += delta;
    CountBuildingDelta(u, delta);
}
