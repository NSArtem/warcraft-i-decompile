/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiCastPointSpell 0x2a774: cast the
 * unit's area spell (rain of fire 0x1a or cloud of poison 0x1b, the caller
 * stores it in spell_order) at the AI attack point.  Only when the unit is
 * within 25 tiles of the point; scans an 11x11 box there for an enemy and
 * casts at a tile jittered by +-2 around it.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x2a774 */
int AiCastPointSpell(Unit *u)
{
    int x, y, w, h;
    Unit **cell;
    int i, j;

    if (ai_attack_point.x == -1)
        return 0;
    if (ai_attack_point.y == -1)
        return 0;
    if (fn_13270((short *)&ai_attack_point, u) > 0x19)
        return 0;
    x = ai_attack_point.x;
    y = ai_attack_point.y;
    ClipBox(&x, &y, &w, &h, 0x0b);
    cell = &object_map[y * 64 + x];
    for (i = 0; i < h; i++) {
        for (j = 0; j < w; j++) {
            Unit *v = *cell++;
            if (v == 0)
                continue;
            if (hostility[u->owner * 5 + v->owner] == 0)
                continue;
            if ((v->flags & 0x207) != 0)
                continue;
            UnitOrderTarget(u, v->tx + GameRandom(0x1f) % 5 - 2,
                            v->ty + GameRandom(0x20) % 5 - 2, 0, fn_21168);
            return 1;
        }
        cell += 0x40 - w;
    }
    return 0;
}
