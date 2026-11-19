/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiScoutStep 0x2aefc: sweep the map.
 * The per-player pair ai_home_point/ai_sweep_point is a growing search
 * rectangle: starting at the player's home, one corner moves toward (0,0) and
 * the other toward (63,63).  The routine walks the rows/columns of that
 * rectangle, tests tiles with fn_2bb7c and orders the unit to the first
 * walkable tile.  Returns 1 when it ordered the unit.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x2aefc */
int AiScoutStep(Unit *u)
{
    Point *from = &ai_home_point[u->owner];
    Point *to = &ai_sweep_point[u->owner];
    Point p;
    int dir, n;

    if (from->x == -1)
        return 0;
    do {
        p = *from;
        for (dir = 0; dir < 4; dir++) {
            int len;
            if ((dir & 1) != 0)
                len = to->y - from->y;
            else
                len = to->x - from->x;
            len++;
            for (n = 0; n < len; n++) {
                if (fn_2bb7c(&p)) {
                    UnitOrderTarget(u, p.x, p.y, 0, fn_21094);
                    return 1;
                }
                p.x += step4_dx[dir];
                p.y += step4_dy[dir];
            }
            p.x -= step4_dx[dir];
            p.y -= step4_dy[dir];
        }
        if (from->x > 0)
            from->x--;
        if (from->y > 0)
            from->y--;
        if (to->x < 0x3f)
            to->x++;
        if (to->y < 0x3f)
            to->y++;
    } while (from->x != 0 || from->y != 0 || to->x != 0x3f || to->y != 0x3f);
    from->x = -1;
    return 0;
}
