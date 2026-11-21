/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned short scenario_race;
extern unsigned short scenario_race_enemy;
extern unsigned short setup_changed;
extern unsigned char setup_return_state;
extern unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);

/* @0x14fe4 */
void SetRacesDialog(void)
{
    unsigned long r[2];
    unsigned short id;

    if (dat_516ae == 0 || own_campaign != 0) {
        id = 0x196;
        r[0] = scenario_race;
        r[1] = scenario_race_enemy;
    } else {
        id = 0x197;
        r[0] = scenario_race_enemy;
        r[1] = scenario_race;
    }
    if (DialogRun(id, 0, 0x46, 0x10, (void **)r) == 0) {
        if (dat_516ae == 0 || own_campaign != 0) {
            if (scenario_race != r[0] || scenario_race_enemy != r[1]) {
                setup_changed = 1;
                setup_return_state = 5;
            }
            scenario_race = (unsigned short)r[0];
            scenario_race_enemy = (unsigned short)r[1];
        } else {
            if (scenario_race != r[1] || scenario_race_enemy != r[0]) {
                setup_changed = 1;
                setup_return_state = 5;
            }
            scenario_race = (unsigned short)r[1];
            scenario_race_enemy = (unsigned short)r[0];
        }
    }
}
