/* codegen-compiler: 10.0a */
/* mod_295d0.  AiWanderStep 0x29bac: face a random direction and step one tile
 * that way, clamped to the map, then order the unit to that tile.  The point
 * is updated in place.  Called by AiGuardStartArea 0x29f40.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x29bac */
void AiWanderStep(Unit *u, Point p)
{
    int d;

    d = fn_19478(0x19) & 7;
    p.x += dir_dx[d] * 4 + 1;
    p.y += dir_dy[d] * 4 + 1;
    if (p.x < 0)
        p.x = 0;
    else if (p.x >= 0x40)
        p.x = 0x3f;
    if (p.y < 0)
        p.y = 0;
    else if (p.y >= 0x40)
        p.y = 0x3f;
    UnitOrderTarget(u, p.x, p.y, 0, fn_20f30);
}
