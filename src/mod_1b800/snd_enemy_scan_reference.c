/* codegen-compiler: 10.0a */
/* mod_1b800 (reference C, not T3).  SndEnemyScan 0x1bd64: look for an enemy
 * unit in the 17x17 tiles around the player's town hall and play 'enemy
 * approaching' when one first shows up.  Called by SndTick.
 *
 * T3 blocker (regalloc): same instruction sequence, with the clip and loop
 * shapes matching; the original keeps the town-hall x in edx, x in eax, y in ebp
 * (`mov edx,[0x50e66]; sar edx,16; lea eax,[edx-8]`), we put them in ebx/edx/eax
 * (the same difference as UnitAlertSuppressArea).  Tried: all 24 declaration
 * orders of x,y,w,h, `h = w = 17`, an `unsigned short`/`int` id local for the
 * cue (the original builds it with `sete al; and eax,0xff` where we emit
 * `xor ah,ah`).  First difference at +0x18.
 * See docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

#define HOME_X (*(int *)((char *)&player_home_point[0].x - 2) >> 16)
#define HOME_Y (*(int *)((char *)&player_home_point[0].y - 2) >> 16)

/* @0x1bd64 */
void SndEnemyScan(void)
{
    unsigned short found = 0;
    int x, y, w, h, r, c;
    Unit **p;

    if (player_town_hall[0] == 0)
        return;
    x = HOME_X - 8;
    y = HOME_Y - 8;
    h = w = 17;
    if (x < 0) {
        w = x + 17;
        x = 0;
    } else if (x + 17 >= 64) {
        w = 64 - x;
    }
    if (y < 0) {
        h = y + 17;
        y = 0;
    } else if (y + 17 >= 64) {
        h = 64 - y;
    }
    p = object_map + y * 64 + x;
    for (r = 0; r < h; r++) {
        for (c = 0; c < w; c++, p++) {
            Unit *u = *p;

            if (u != 0 && (u->flags.w & 0x207) == 0 &&
                hostility[u->owner] != 0 && u->timer36 == 0) {
                found = 1;
                break;
            }
        }
        if (found != 0)
            break;
        p += 64 - w;
    }
    if (found != 0 && snd_enemy_near == 0) {
        if (scenario_race == scenario_race_enemy)
            snd_enemy_alt = 0;
        SndEvent(0x14 + (snd_enemy_alt == 0), 0);
        snd_enemy_alt = (snd_enemy_alt == 0);
        snd_enemy_scan_timer = 1000;
    } else {
        snd_enemy_scan_timer = 200;
    }
    snd_enemy_near = found;
}
