/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiChooseAttackPoint 0x29644: choose the
 * AI's attack target area.  Counts the *player 0* units on a 4x4 grid over the
 * map (a building counts 4, a unit 1) and stores the centre of the fullest
 * cell, in pixels, in ai_attack_point.  See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x29644 */
void AiChooseAttackPoint(void)
{
    short grid[16];
    Point best;
    int bestv;
    int i, j, w;
    Unit *u;

    for (i = 0; i < 16; i++)
        grid[i] = 0;
    u = unit_array;
    for (i = 0; i < 200; i++) {
        if ((u->flags & 0x207) != 0)
            goto next;
        if (u->owner != 0)
            goto next;
        w = (u->type >= 0x20 && u->type <= 0x32) ? 4 : 1;
        grid[(u->ty >> 4) * 4 + (u->tx >> 4)] += w;
next:
        u++;
    }
    bestv = -1;
    best.x = 0;
    best.y = 0;
    for (i = 0; i < 4; i++)
        for (j = 0; j < 4; j++)
            if (bestv < grid[i * 4 + j]) {
                bestv = grid[i * 4 + j];
                best.x = j;
                best.y = i;
            }
    ai_attack_point.x = best.x * 16 + 8;
    ai_attack_point.y = best.y * 16 + 8;
}
