/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiCastRaiseDead 0x2a3cc: the
 * Necrolyte's raise dead.  Finds a corpse (type 0x33 with the 0x2 flag) within
 * 10 tiles (squared distance) and casts spell 0x14 at its tile.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x2a3cc */
int AiCastRaiseDead(Unit *u)
{
    Unit *v = unit_array;
    int i;

    for (i = 0; i < 200; i++) {
        int dx, dy;
        if (v->type != 0x33)
            goto next;
        if ((v->flags & 2) == 0)
            goto next;
        if ((v->flags & 0x20d) != 0)
            goto next;
        dx = v->tx - u->tx;
        dy = v->ty - u->ty;
        if (dx * dx + dy * dy >= 0x64)
            goto next;
        spell_order = 0x14;
        UnitOrderTarget(u, v->tx, v->ty, 0, fn_21168);
        return 1;
next:
        v++;
    }
    return 0;
}
