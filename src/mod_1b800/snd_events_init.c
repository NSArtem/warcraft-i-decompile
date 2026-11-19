/* codegen-compiler: 10.0a */
/* mod_1b800.  SndEventsInit 0x1b8d4: reset the sound-event state at a scenario
 * start and load the race's sound table (or free it with in_game 0).  See
 * docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1b8d4 */
void SndEventsInit(int in_game)
{
    snd_select_cooldown = 0;
    snd_enemy_near = 0;
    snd_enemy_alt = 1;
    snd_last_selected = 0;
    snd_select_clicks = 0;
    snd_enemy_scan_timer = 0x190;
    if ((unsigned short)in_game != 0)
        SndLoadTable(snd_event_table[scenario_race]);
    else
        SndLoadTable(0);
}
