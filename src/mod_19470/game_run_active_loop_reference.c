/* codegen-compiler: 10.0a */
#include "mod_19470.h"
#include <time.h>

extern void MissionEndTick(int);

/* 0x19810 */
void GameRunActiveLoop(void)
{
    unsigned short phase;
    unsigned long next_tick = 0;
    unsigned long now;
    short simulation_due;

    (void)*(volatile unsigned short *)&game_tick_delay_phase;
    while ((*(const volatile long *)&game_mode_dword_low >> 16) == 3) {
        ++minimap_redraw_state;
        now = (unsigned long)clock();
        if (game_speed_cache != prefs_block[0] || crit_error_flag != 0) {
            crit_error_flag = 0;
            game_speed_cache = prefs_block[0];
            next_tick = now;
        }
        phase = *(volatile unsigned short *)&game_tick_delay_phase;
        if (now >= next_tick) {
            next_tick += game_tick_delays[prefs_block[0]][phase];
            phase ^= 1U;
            simulation_due = 1;
        } else {
            simulation_due = 0;
        }
        game_tick_delay_phase = phase;
        if (simulation_due != 0)
            --packet_tick_countdown;
        GameUpdateFrame(simulation_due, (short)(packet_tick_countdown == 0));
        if (simulation_due != 0 && packet_tick_countdown == 0)
            packet_tick_countdown = packet_tick_intervals[prefs_block[0]][net_link_speed];
        MissionEndTick(0);
    }
    (void)*(volatile unsigned short *)&game_tick_delay_phase;
}
