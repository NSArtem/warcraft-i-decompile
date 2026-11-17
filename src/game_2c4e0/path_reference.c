/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_2c4e0 (PATH.C, 0x2c4e0..0x2ced0), game code, "OPT" style.
 * Reference C for PathPeekStep (0x2c4e0): three spellings of the same logic
 * tried against OW2.  All are near misses: OW2 keeps the path index and the
 * direction in 8-bit registers, or loads them through a pointer and masks,
 * where the original zero-extends both into ebx and compares 32-bit (the
 * first differing instructions are in the symbol entry's t3_blocker; _a does
 * reproduce the `mov dl,path[i]; xor ebx,ebx; mov bl,dl` extraction of the
 * direction after an earlier difference).  Behaviour-checked as compiled C
 * against the original: tests/test_game_2c4e0.py::test_t4_path_peek_step.
 * Not built; see docs/subsystems/game_2c4e0.md. */
#include "game_2c4e0.h"

extern signed char dir_dx[8];       /* 0x50f80 */
extern signed char dir_dy[8];       /* 0x50f88 */

/* @0x2c4e0 */
int PathPeekStep_a(Unit *u, Point *out)
{
    unsigned char i = u->path_idx;
    unsigned char d;
    if ((int)i >= 20) return 0;
    d = u->path[i];
    if ((int)d == 0xfe) return 0;
    out->x = u->tx + dir_dx[d];
    out->y = u->ty + dir_dy[d];
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
    out->x = u->tx + dir_dx[dd];
    out->y = u->ty + dir_dy[dd];
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
    out->x = u->tx + dir_dx[dd];
    out->y = u->ty + dir_dy[dd];
    return 1;
}
