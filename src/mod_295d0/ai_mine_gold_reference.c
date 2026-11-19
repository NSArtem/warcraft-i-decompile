/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiMineGold 0x2ac38: send a worker to
 * the best gold mine.  The mine (type 0x32) must still hold gold (+0x54); the
 * score is distance(player home, mine) + distance(player 0 home, mine)/4 +
 * distance(mine, unit), lowest wins.  See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

#define UNIT_GOLD(u) (*(unsigned long *)((char *)(u) + 0x54))   /* 0x54: a gold mine's reserve */

/* @0x2ac38 */
int AiMineGold(Unit *u)
{
    Unit *v = unit_array;
    Unit *best = 0;
    unsigned short best_score = -1;
    int i;

    for (i = 0; i < 200; i++) {
        unsigned score;
        unsigned d1, d2, d3;

        if ((v->flags & 0x207) != 0)
            goto next;
        if (v->type != 0x32)
            goto next;
        if (UNIT_GOLD(v) == 0)
            goto next;
        d1 = fn_13270((short *)&player_home_point[u->owner], v);
        d2 = fn_13270((short *)&player_home_point[0], v);
        d3 = fn_13270(&v->tx, u);
        score = (unsigned short) (d1 + (d2 >> 2) + d3);
        if (best_score <= score)
            goto next;
        best_score = score;
        best = v;
next:
        v++;
    }
    if (best == 0)
        return 0;
    UnitOrderTarget(u, 0, 0, best, fn_21094);
    u->order_flags |= 1;
    ai_work_count[u->owner]++;
    return 1;
}
