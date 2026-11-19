/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiDefendTownHall 0x2a168: when the
 * owner's town hall exists and is damaged, look for an enemy within 30 tiles
 * of the tile next to it (range 10, preference distance 1).
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

extern Unit *AiBestTarget(short *origin, short range, short pref_dist, unsigned char *enemy_row);

/* @0x2a168 */
Unit *AiDefendTownHall(Unit *u)
{
    Unit *hall;
    Unit *t;
    Point p;

    hall = player_town_hall[u->owner];
    if (hall == 0)
        return 0;
    if (hall->hp == unit_max_hp[u->type])
        return 0;
    p = player_home_point[u->owner];
    p.x++;
    p.y++;
    if (fn_13270((short *)&p, u) > 0x1e)
        return 0;
    t = AiBestTarget((short *)&p, 0xa, 1, &hostility[u->owner * 5]);
    return t;
}
