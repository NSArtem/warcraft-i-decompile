/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* MissionEndTick (0x2f7fc): the per-frame poll of the mission-end
 * condition.  force != 0 (the message path that just got the enemy's quit)
 * runs the check immediately; otherwise the 0x140-tick countdown runs. */
#include "mod_2efd0.h"

/* @0x2f7fc */
void MissionEndTick(short force)
{
    if (end_check_timer != 0 && force == 0) {
        end_check_timer--;
        return;
    }
    end_check_timer = 0x140;
    end_screen_action();
}
