/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -5r -zp2 */
/* mod_295d0.  AiGuardStartArea 0x29f40: the AI's
 * last resort for an idle unit - stay near the player's start area.  Only runs
 * when the owner has no town hall and the home point is set; if the unit is
 * inside the 3x3 tiles at the home point (and not yet at its far corner) it
 * steps to a random neighbouring tile.  Returns 1 when it moved the unit.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

extern void AiWanderStep(Unit *u, Point p);    /* 0x29bac */

/* @0x29f40 */
int AiGuardStartArea(Unit *u)
{
    Point home;

    if (player_town_hall[u->owner] != 0)
        return 0;
    home = player_home_point[u->owner];
    if (home.x == 0 && home.y == 0)
        return 0;
    if (u->tx < home.x)
        return 0;
    if (u->ty < home.y)
        return 0;
    if (u->tx >= home.x + 3)
        return 0;
    if (u->ty >= home.y + 3)
        return 0;
    AiWanderStep(u, home);
    return 1;
}
