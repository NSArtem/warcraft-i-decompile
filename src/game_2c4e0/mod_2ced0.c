/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_2ced0 (0x2ced0..0x2efd0), game code, "OPT" style: unit list management, unit
 * creation/destruction, order queue, per-cycle unit update.  Functions here reproduce the
 * original bytes (python3 -m wc1.match / wc1.codegen_sweep); see docs/subsystems/game_2c4e0.md. */
#include "game_2c4e0.h"

extern Unit *draw_list[];            /* 0x5a490 */

/* @0x2cfa8  remove a unit from the null-terminated draw list, closing the gap */
void DrawListRemove(Unit *u)
{
    Unit **p = draw_list;
    if (draw_list[0] == 0)
        return;
    do {
        if (u == *p) {
            do {
                p[0] = p[1];
                p++;
            } while (*p);
            return;
        }
        p++;
    } while (*p);
}

/* @0x2cfd8  insert a unit into the draw list, ordered by tile row */
void DrawListInsert(Unit *u)
{
    Unit **p = draw_list;
    Unit *carry = u;
    if (draw_list[0]) {
        unsigned short f = u->flags & 0x207;
        do {
            Unit *c = *p;
            unsigned short cf = c->flags & 0x207;
            unsigned short ck = cf ? 0 : c->ty;
            unsigned short uk = f ? 0 : carry->ty;
            if (uk <= ck) {
                do {
                    Unit *t = *p;
                    *p = carry;
                    carry = t;
                    p++;
                } while (*p);
                break;
            }
            p++;
        } while (*p);
    }
    *p = carry;
    p++;
    *p = 0;
}
