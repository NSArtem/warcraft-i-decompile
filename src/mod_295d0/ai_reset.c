/* codegen-compiler: 10.0a */
/* mod_295d0 (the computer-opponent AI).  AiReset 0x295d0: clear the AI's
 * per-player counters and timers at scenario start.  Called by the scenario
 * start 0x195ac with its own "resume a saved game" flag: on a resumed game the
 * state comes from the save image, so nothing is cleared.  See
 * docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x295d0 */
void AiReset(int resume)
{
    unsigned short i;

    if (resume != 0)
        return;
    for (i = 0; i < 5; i++) {
        ai_busy_count[i] = 0;
        ai_work_count[i] = 0;
        ai_home_point[i].x = -1;
        ai_site_count[i] = 0;
        ai_helper_count[i] = 0;
    }
    ai_retarget_timer = 1;
    ai_attack_point.y = -1;
    ai_attack_point.x = -1;
    ai_wave_timer = 0x1770;
}
