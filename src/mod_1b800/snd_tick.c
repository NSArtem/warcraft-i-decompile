/* codegen-compiler: 10.0a */
/* mod_1b800.  SndTick 0x1bf40: per-game-tick countdowns of the sound events;
 * runs the enemy-near scan when its timer is out.  Called by 0x197b0.  See
 * docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

extern void SndEnemyScan(void);    /* 0x1bd64 */

/* @0x1bf40 */
void SndTick(void)
{
    if (snd_select_cooldown != 0)
        snd_select_cooldown--;
    if (snd_enemy_scan_timer != 0)
        snd_enemy_scan_timer--;
    else
        SndEnemyScan();
}
