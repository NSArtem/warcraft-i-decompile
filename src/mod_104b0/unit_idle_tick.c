/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitIdleTick (0x10ee8): the per-tick body of the stop order (order 2): try
 * to retaliate first, then let workers work, finished buildings restart their
 * production, the AI scans for targets and idle units wait out their timer.
 * See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c */
extern unsigned short dat_503a[];              /* 0x503a per-building rebuild delay */
extern unsigned short scenario_unit_mask;      /* 0x50004 */

extern int UnitRetaliate(Unit *u, int is_human);              /* 0x10d34 */
extern int fn_2b064(Unit *u);                                 /* 0x2b064 */
extern void RestartProduction(Unit *u);                       /* 0x11990 */
extern void fn_2a8f4(Unit *u);                                /* 0x2a8f4 */
extern void fn_2ab54(Unit *u);                                /* 0x2ab54 */
extern int UnitAcquireTarget(Unit *u, int chase, void (*cb)(Unit *)); /* 0x10908 */
extern void fn_20fac(Unit *u);                                /* 0x20fac */

/* @0x10ee8 */
void UnitIdleTick(Unit *u)
{
    int human = (dat_5008c[u->owner] == 1);

    if (UnitRetaliate(u, human) != 0)
        return;
    if (u->type == 2 || u->type == 3) {
        if (human)
            fn_2b064(u);
        return;
    }
    if (u->type >= 0x20 && u->type <= 0x32) {
        if (!human)
            return;
        if ((u->flags.w & 0x80) == 0)
            return;
        if (u->word4a == 1) {
            RestartProduction(u);
            return;
        }
        if (u->word4a == 0) {
            u->word4a = dat_503a[u->type - 0x20];
            return;
        }
        u->word4a--;
        return;
    }
    if (u->type >= 0x10 && u->type <= 0x12)
        return;
    if (human) {
        if (u->type >= 0xa && u->type <= 0xe) {
            fn_2a8f4(u);
            return;
        }
        if (u->timer36 == 0)
            fn_2ab54(u);
    } else {
        if (u->timer36 == 0)
            UnitAcquireTarget(u, 1, fn_20fac);
    }
}
