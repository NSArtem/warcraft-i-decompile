/* codegen-compiler: 10.0a */
#include "mod_13b30_f1.h"

extern unsigned short player_active_buildings[4];
extern unsigned short dead_buildings[5];
extern void ScoreAddForBuildings(struct Unit *u);
extern void ScoreSubForBuildings(struct Unit *u);

/* @0x13b4c */
void CountBuildingDelta(struct Unit *u, short delta)
{
    player_active_buildings[*((unsigned char *)u + 0x1e)] += delta;
    if (delta > 0) {
        ScoreAddForBuildings(u);
    } else {
        dead_buildings[*((unsigned char *)u + 0x1e)]++;
        ScoreSubForBuildings(u);
    }
}
