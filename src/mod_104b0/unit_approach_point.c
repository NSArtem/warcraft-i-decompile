/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitApproachPoint (0x107a0): a tile in front of an enemy, jittered by the
 * RNG and clamped to the map, used as the destination of the "go and attack"
 * order that retaliation issues.  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern signed char dir_dx[];                   /* 0x50f80 */
extern signed char dir_dy[];                   /* 0x50f88 */
extern int fn_19478(unsigned id);              /* 0x19478 LCG */

/* @0x107a0  (u = eax, out = ebx, enemy = edx) */
void UnitApproachPoint(Unit *u, Unit *enemy, Point *out)
{
    unsigned d = enemy->facing;

    *(unsigned long *) out = *(unsigned long *) &u->tx;
    out->x += dir_dx[d] * 4 + (fn_19478(0xe) & 7) - 2;
    out->y += dir_dy[d] * 4 + (fn_19478(0xf) & 7) - 2;
    if (out->x < 0)
        out->x = 0;
    else if (out->x >= 0x40)
        out->x = 0x3f;
    if (out->y < 0) {
        out->y = 0;
        return;
    }
    if (out->y >= 0x40)
        out->y = 0x3f;
}
