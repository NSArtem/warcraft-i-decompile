/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * fn_222d8 (0x222d8, PLACEBOX.C) = OrderArgInRange: test the unit's *current*
 * order against its target with OrderTargetInRange.  The symbol entry lives
 * in mod_104b0.toml (placeholder fn_222d8); reported, not wired here. */
#include "mod_20c30.h"

int fn_2220c(Unit *u, unsigned char arg);              /* 0x2220c */

/* @0x222d8 */
int fn_222d8(Unit *u)
{
    return fn_2220c(u, u->order);
}
