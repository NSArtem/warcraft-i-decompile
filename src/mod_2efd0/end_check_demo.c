/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndCheckDemo (0x2f754): the attract-mode and no-objective end condition -
 * as soon as either side has nothing left the mission returns to the main
 * menu instead of showing a win/lose screen. */
#include "mod_2efd0.h"

/* @0x2f754 */
void EndCheckDemo(void)
{
    if (player_active_men[0] == 0 && player_building_count[0] == 0)
        goto set;
    if (player_active_men[1] != 0 || player_building_count[1] != 0)
        return;
set:
    end_screen_action = MissionToMenu;
}
