/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_2ced0 (UNIT.C, 0x2ced0..0x2efd0), game code, "OPT" style.
 * Reference C for the draw-list sort/insert (0x2ced0, 0x2cfd8): same
 * algorithm as the original, but the key reads ty as a short. The original
 * loads the tile dword and shifts (`mov eax,[u+0xa]; sar eax,0x10`) and
 * compares 16-bit keys, so these stay near misses (not built).
 * DrawListRemove (0x2cfa8) matches and lives in draw_list_remove.c.
 * See docs/subsystems/game_2c4e0.md. */
#include "game_2c4e0.h"

extern Unit *draw_list[];            /* 0x5a490 */

/* @0x2ced0  bubble-sort the list by the draw key */
void DrawListSort(void)
{
    Unit **p = draw_list;
    if (draw_list[0] == 0 || draw_list[1] == 0)
        return;
    do {
        Unit *a = p[0];
        Unit *b = p[1];
        unsigned short ka = (a->flags.w & 0x207) ? 0 : a->ty;
        unsigned short kb = (b->flags.w & 0x207) ? 0 : b->ty;
        if (kb < ka) {
            Unit **q = p;
            do {
                Unit *t = q[1];
                q[1] = q[0];
                q[0] = t;
                q--;
                if (q <= draw_list)
                    break;
            } while (((q[1]->flags.w & 0x207) ? 0 : q[1]->ty) <
                     ((q[0]->flags.w & 0x207) ? 0 : q[0]->ty));
        }
        p++;
    } while (p[1]);
}

/* @0x2cfd8  insert a unit into the draw list, ordered by draw key */
void DrawListInsert(Unit *u)
{
    Unit **p = draw_list;
    Unit *carry = u;
    if (draw_list[0]) {
        unsigned short f = u->flags.w & 0x207;
        do {
            Unit *c = *p;
            unsigned short cf = c->flags.w & 0x207;
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
