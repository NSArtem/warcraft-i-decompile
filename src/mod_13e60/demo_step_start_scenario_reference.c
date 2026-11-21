/* codegen-compiler: 10.0a */
#include "mod_13e60.h"

extern short game_mode;
extern unsigned short scenario_number;
extern unsigned short custom_game;
extern unsigned short own_campaign;
extern unsigned short net_play_flag;
extern short screen_mode;

/* @0x13ea0 */
int DemoStepStartScenario(void)
{
    int one;

    game_mode = 3;
    scenario_number = demo_steps[demo_step_index].scenario;
    net_play_flag = 0;
    one = 1;
    screen_mode = one;
    custom_game = 0;
    own_campaign = one;
    return one;
}
