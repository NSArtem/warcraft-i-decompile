/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * UnitClearTargets (0x2207c, PLACEBOX.C): drop the target and the last
 * attacker once they are dead (flags & 0x20f) or have a running timer
 * (+0x36).  Returns 0 when it dropped the target, 1 otherwise.
 *
 * The symbol entry for 0x2207c lives in mod_104b0.toml (placeholder
 * fn_2207c); the C is reported, not wired from here. */
#include "mod_20c30.h"

/* @0x2207c */
unsigned short fn_2207c(Unit *u)
{
    Unit *t = u->target;

    if (t != 0) {
        if ((t->flags.w & 0x20f) != 0 || t->timer36 != 0) {
            if (t == u->attacker)
                u->attacker = 0;
            u->target = 0;
            return 0;
        }
        t = u->attacker;
        if (t != 0) {
            if ((t->flags.w & 0x20f) != 0 || t->timer36 != 0)
                u->attacker = 0;
        }
    }
    return 1;
}
