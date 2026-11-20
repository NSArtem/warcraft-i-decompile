/* codegen-compiler: 10.0a */
#include "game_2c4e0.h"

extern int PathPeekStep(Unit *u, Point *out);
extern unsigned short fn_13348(short x, int y, unsigned mask);

/* @0x2c538 */
int PathAdvanceFacing(Unit *u, Point *p)
{
    PathPeekStep(u, p);
    if (fn_13348(p->x, *(long *)p >> 16, 0x3cc) != 0) {
        return 0;
    }
    u->facing = u->path[u->path_idx++];
    return 1;
}
