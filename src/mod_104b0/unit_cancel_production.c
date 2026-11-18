/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * UnitCancelProduction (0x116a8) - T3-matched: a busy building
 * (flags2 bit 0x10) is told to cancel (bit 0x20), which the production
 * handlers test.  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

/* @0x116a8 */
void UnitCancelProduction(Unit *u)
{
    unsigned f = u->flags2 & 0x10;

    if (f != 0)
        u->flags2 |= 0x20;
}
