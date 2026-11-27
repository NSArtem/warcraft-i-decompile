/* codegen-compiler: 10.0a */
#include "mod_19470.h"

extern int GameRandom(int);

/* 0x194a8: resolves the custom map and applies the scenario base at 0x1957f. */
void GameResolveCustomScenario(void)
{
    unsigned base;

    if (custom_game != 0) {
        custom_map_group = *(const unsigned short *)&map_choice_params[5];
        custom_map_index = *(const unsigned short *)&map_choice_params[0];
    }

    if (custom_map_group == 3) {
        switch (custom_map_index) {
        case 0:
            custom_map_group = (unsigned short)((unsigned char)GameRandom(0x1d) & 1);
            break;
        case 1:
            custom_map_group = (unsigned short)(GameRandom(0x1c) % 3);
            break;
        case 2:
            custom_map_group = 0;
            break;
        case 3:
            custom_map_group = 1;
            break;
        case 4:
            custom_map_group = 2;
            break;
        }
        custom_map_index = (unsigned short)(GameRandom(0x31) % 7);
    }

    scenario_number = (unsigned short)(custom_map_group * 7 + custom_map_index);
    base = net_play_flag != 0 ? 0x95 : 0xaa;
    scenario_number = (unsigned short)((unsigned)scenario_number + base);
}
