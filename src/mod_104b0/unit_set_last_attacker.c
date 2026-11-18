/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * UnitSetLastAttacker (0x10ce0) - T3-matched.  Records who hit a unit, for
 * the retaliation code (0x10d34 / 0x10b1c / 0x10908).  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char hostility[];        /* 0x51883, 5x5, 1 = enemy */

/* @0x10ce0  (u = eax, attacker = edx) */
void UnitSetLastAttacker(Unit *u, Unit *attacker)
{
    unsigned rel = u->owner * 5 + attacker->owner;

    if (hostility[rel] != 0) {
        unsigned f = u->flags.w & 0x207;

        if (f == 0) {
            if (u->attacker != 0) {
                unsigned g = u->attacker->flags.w & 0x207;

                if (g == 0)
                    return;
            }
            u->attacker = attacker;
        }
    }
}
