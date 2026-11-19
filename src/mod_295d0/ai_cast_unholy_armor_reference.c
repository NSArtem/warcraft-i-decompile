/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiCastUnholyArmor 0x2a624: the
 * Necrolyte's unholy armor.  Scans the 21x21 tiles around the unit for a
 * friendly, damaged unit that is in a fight (has an attacker) and casts spell
 * 0x15 on it.  See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x2a624 */
int AiCastUnholyArmor(Unit *u)
{
    int x, y, w, h;
    Unit **cell;
    int i, j;

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
            if (v->type >= 0x20 && v->type <= 0x32)
                continue;
            if (v->timer38 != 0)
                continue;
            if (v->type == 0x1c)
                continue;
            if (v->type == 5)
                continue;
            if (v->attacker == 0)
                continue;
            if (v->hp > unit_max_hp[v->type] / 2)
                continue;
            spell_order = 0x15;
            UnitOrderTarget(u, 0, 0, v, fn_21168);
            return 1;
        }
        cell += 0x40 - w;
    }
    return 0;
}
