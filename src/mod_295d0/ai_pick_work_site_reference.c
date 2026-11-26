/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiPickWorkSite 0x29c58: send a unit to
 * a work site picked at random.  The table work_sites starts with a list of
 * {weight, site} word pairs; a roll of Random(0x1a) % 100 picks one by weight,
 * a 0xffff weight means "no site" (the unit just stops).  The chosen site's
 * record gives the x/y the unit is ordered to.  See
 * docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x29c58 */
void AiPickWorkSite(Unit *u)
{
    unsigned short *p = work_sites;
    int r;
    int i;
    unsigned site;

    r = GameRandom(0x1a) % 100;
    for (i = 0; r > p[i]; i += 2)
        r -= p[i];
    if (p[i] == 0xffff) {
        u->order_flags = 4;
        return;
    }
    u->order_flags = 0x10;
    site = p[i + 1];
    u->work_site = site | 0x8000;
    u->work_x = p[site + 1];
    u->work_y = p[site + 2];
    UnitOrderTarget(u, u->work_x, u->work_y, 0, fn_20f30);
}
