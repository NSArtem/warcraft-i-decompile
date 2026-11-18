/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitMoveOrderCheck (0x11004): the move order's first step - a human unit
 * that is not a worker and not a spellcaster scans for a target on the way,
 * everything else only retaliates.  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5008c[];              /* 0x5008c */
extern int UnitRetaliate(Unit *u, int is_human);              /* 0x10d34 */
extern int UnitAcquireTarget(Unit *u, int chase, void (*cb)(Unit *)); /* 0x10908 */
extern void fn_20f30(Unit *u);                                /* 0x20f30 */

/* @0x11004 */
int UnitMoveOrderCheck(Unit *u)
{
    int type = u->type;
    int worker = (type >= 2 && type <= 3);

    if (!worker) {
        if (u->order_next2 != 6) {
            u->attacker = 0;
            return 0;
        }
    }
    if (dat_5008c[u->owner] != 1)
        goto retaliate;
    if (type == 2 || type == 3)
        return 0;
    if (type >= 0xa && type <= 0xd)
        goto retaliate;
    return UnitAcquireTarget(u, 0, fn_20f30);
retaliate:
    if (UnitRetaliate(u, 0) != 0)
        return 1;
    return 0;
}
