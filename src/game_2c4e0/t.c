/* codegen-flags: -s -ot -ol -4r -zp2 */
#include "game_2c4e0.h"
extern signed char dat_50f80[8];
extern signed char dat_50f88[8];

/* @0x2c4e0 */
int PathPeekStep_a(Unit *u, Point *out)
{
    unsigned char i = u->path_idx;
    unsigned char d;
    if ((int)i >= 20) return 0;
    d = u->path[i];
    if ((int)d == 0xfe) return 0;
    out->x = u->tx + dat_50f80[d];
    out->y = u->ty + dat_50f88[d];
    return 1;
}
/* @0x2c4e0 */
int PathPeekStep_b(Unit *u, Point *out)
{
    unsigned char *p = &u->path_idx;
    int i = *p;
    unsigned char d;
    int dd;
    if (i >= 20) return 0;
    d = u->path[i];
    dd = d;
    if (dd == 0xfe) return 0;
    out->x = u->tx + dat_50f80[dd];
    out->y = u->ty + dat_50f88[dd];
    return 1;
}
/* @0x2c4e0 */
int PathPeekStep_c(Unit *u, Point *out)
{
    volatile unsigned char *p = &u->path_idx;
    int i = *p;
    unsigned char d;
    int dd;
    if (i >= 20) return 0;
    d = u->path[i];
    dd = d;
    if (dd == 0xfe) return 0;
    out->x = u->tx + dat_50f80[dd];
    out->y = u->ty + dat_50f88[dd];
    return 1;
}
