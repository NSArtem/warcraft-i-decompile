/* codegen-compiler: 10.0a */
#include "mod_13b30_f1.h"

struct HomePt { short x; short y; };

extern void *player_town_hall[5];
extern unsigned short player_building_count[5];
extern unsigned short player_active_buildings[4];
extern unsigned short player_mills[5];
extern unsigned short player_blacksmiths[5];
extern unsigned short player_stables[5];
extern unsigned short player_unit_cap[5];
extern unsigned short player_town_hall_count[5];
extern unsigned short player_food[5];
extern unsigned short player_active_men[4];
extern unsigned short player_worker_count[5];
extern unsigned short player_summoned[5];
extern unsigned short player_unit_count[5];
extern struct HomePt player_home_point[5];
extern unsigned short training_count[5];
extern unsigned short dead_men[5];
extern unsigned short dead_buildings[5];
extern unsigned short dat_50dac[5];
extern unsigned short dat_50db6[5];
extern unsigned long harvested_gold[5];
extern unsigned long harvested_lumber[5];

/* @0x13d04 */
void PlayerStatsReset(int keep_totals)
{
    int i;

    for (i = 0; i < 5; i++) {
        player_town_hall[i] = 0;
        player_building_count[i] = 0;
        player_active_buildings[i] = 0;
        player_stat_58e32[i] = 0;
        player_mills[i] = 0;
        player_blacksmiths[i] = 0;
        player_stables[i] = 0;
        player_unit_cap[i] = 0;
        player_town_hall_count[i] = 0;
        player_food[i] = 0;
        player_active_men[i] = 0;
        player_worker_count[i] = 0;
        player_summoned[i] = 0;
        player_unit_count[i] = 0;
        if (keep_totals == 0) {
            player_home_point[i].y = 0;
            player_home_point[i].x = 0;
            training_count[i] = 0;
            player_stat_50d98[i] = 0;
            dead_men[i] = 0;
            dead_buildings[i] = 0;
            dat_50dac[i] = 0;
            dat_50db6[i] = 0;
            harvested_gold[i] = 0;
            harvested_lumber[i] = 0;
        }
    }
}
