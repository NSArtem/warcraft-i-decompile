/* codegen-compiler: 10.0a */
#include "mod_13b30_f1.h"

extern unsigned short player_food[5];

/* @0x13b7c */
void CountFoodBuildingDelta(struct Unit *u, short delta)
{
    player_food[*((unsigned char *)u + 0x1e)] += delta * 4;
    CountBuildingDelta(u, delta);
}
