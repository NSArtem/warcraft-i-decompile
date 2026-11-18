/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_110a0 (0x110a0..0x11530), the attack order handlers, "OPT" style.
 * UnitWanderStep (0x11298): with no target left, face a random direction and
 * step to the first free neighbouring tile.  The direction list at 0x110a0 is
 * {0, 1, -1, 0}; the original walks it from index 0, so only the "keep the
 * facing" entry is ever tried (the loop has no index increment).  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern signed char dir_dx[];                   /* 0x50f80 */
extern signed char dir_dy[];                   /* 0x50f88 */
extern signed char wander_direction_offsets[]; /* 0x110a0 */

extern unsigned char fn_1def0(Unit *u);                        /* 0x1def0 */
extern unsigned short fn_13348(short x, short y, unsigned mask); /* 0x13348 */
extern void UnitOrderTarget(Unit *u, short x, short y, Unit *target, void (*fn)(Unit *)); /* 0x2e100 */
extern void fn_20eb4(Unit *u);                                /* 0x20eb4 */

/* @0x11298 */
int UnitWanderStep(Unit *u)
{
    unsigned d;

    u->facing = fn_1def0(u);
    d = (u->facing + wander_direction_offsets[0]) & 7;
    {
        int x = u->tx + dir_dx[d];
        int y = u->ty + dir_dy[d];

        if (x < 0x40 && y < 0x40 && fn_13348(x, y, 0x3cc) == 0) {
            UnitOrderTarget(u, x, y, 0, fn_20eb4);
            return 1;
        }
    }
    return 0;
}
