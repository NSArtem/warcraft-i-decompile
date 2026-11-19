/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiCastInvisibility 0x2a48c: the
 * Cleric's invisibility.  Scans the 21x21 tiles around the unit for a healthy
 * moving Knight/Archer of its own side, sends that unit to the AI's attack
 * point and casts spell 0x13 (invisibility) on it.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x2a48c */
int AiCastInvisibility(Unit *u)
{
    int x, y, w, h;
    Unit **cell;
    int i, j;

    if (ai_attack_point.x == -1)
        return 0;
    if (ai_attack_point.y == -1)
        return 0;
    x = u->tx;
    y = u->ty;
    ClipBox(&x, &y, &w, &h, 0x15);
    cell = &object_map[y * 64 + x];
    for (i = 0; i < h; i++) {
        for (j = 0; j < w; j++) {
            Unit *v = *cell++;
            if (v == 0)
                continue;
            if (hostility[u->owner * 5 + v->owner] != 0)
                continue;
            if ((v->flags & 0x207) != 0)
                continue;
            if (v->timer36 != 0)
                continue;
            if (v->order != 3)
                continue;
            if (v->type != 6 && v->type != 8)
                continue;
            if (v->hp <= unit_max_hp[v->type] / 2)
                continue;
            UnitOrderTarget(v, ai_attack_point.x, ai_attack_point.y, 0, fn_20eb4);
            spell_order = 0x13;
            UnitOrderTarget(u, 0, 0, v, fn_21168);
            return 1;
        }
        cell += 0x40 - w;
    }
    return 0;
}
