/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndScreenSoundId (0x2fa30): pick the sound/track id of the win-lose
 * screen - a fixed id for the defeat screen, otherwise a random entry of
 * the 6-track table that matches the mission's races. */
#include "mod_2efd0.h"

/* @0x2fa30 */
int EndScreenSoundId(void)
{
    unsigned short *table;

    if (game_mode == 7) {
        GameRandom(0xb);
        return 2 + (scenario_race != 0);
    }
    if (scenario_race == scenario_race_enemy) {
        if (scenario_race == 1)
            table = end_music_win;
        else
            table = end_music_lose2;
    } else {
        if (scenario_race == 1)
            table = end_music_win2;
        else
            table = end_music_lose;
    }
    return table[GameRandom(0xb) % 6];
}
