/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_2ced0 (UNIT.C, 0x2ced0..0x2efd0), game code, "OPT" style.
 * DrawListRemove (0x2cfa8) - T3-matched; see docs/subsystems/game_2c4e0.md.
 * The neighbouring DrawListSort/DrawListInsert are kept as reference C in
 * draw_list_reference.c (same code, but OW2 register allocation differs). */
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
