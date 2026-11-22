/* codegen-compiler: 10.0a */
#include "mod_13b30_f1.h"

extern void *player_town_hall[5];
extern unsigned long player_home_point[5];
extern unsigned short player_food[5];

/* @0x13bb4 */
void CountTownHallFullDelta(struct Unit *u, short delta)
{
    if (delta > 0) {
        player_town_hall[*((unsigned char *)u + 0x1e)] = u;
        player_home_point[*((unsigned char *)u + 0x1e)] = *(unsigned long *)((unsigned char *)u + 0xa);
    } else {
        player_town_hall[*((unsigned char *)u + 0x1e)] = 0;
    }
    player_food[*((unsigned char *)u + 0x1e)] += delta;
    CountTownHallDelta(u, delta);
}
