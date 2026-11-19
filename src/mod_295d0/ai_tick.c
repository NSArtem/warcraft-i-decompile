/* codegen-compiler: 10.0a */
/* mod_295d0.  AiTick 0x29a08: the AI's periodic tick.  It counts down the
 * target-point timer (re-running AiChooseAttackPoint every 0x320 ticks) and
 * the wave timer; when the wave timer expires it picks the next interval from
 * the mission-condition word and releases the AI's workers from their work
 * sites.  Called once per game tick by 0x197b0.  See
 * docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

extern void AiChooseAttackPoint(void);         /* 0x29644 */
extern void AiResetWorkSites(void);            /* 0x29954 */

/* @0x29a08 */
void AiTick(void)
{
    if (--ai_retarget_timer == 0) {
        ai_retarget_timer = 0x320;
        AiChooseAttackPoint();
    }
    if (--ai_wave_timer == 0) {
        if ((scenario_objectives & 0x84) != 0) {
            ai_wave_timer = 0x15e;
            ai_tick_count++;
        } else if ((scenario_objectives & 0x40) != 0) {
            ai_wave_timer = 0x1770;
            ai_tick_count++;
        } else {
            ai_wave_timer = -1;
        }
        AiResetWorkSites();
    }
}
