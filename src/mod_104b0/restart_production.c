/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * RestartProduction (0x11990) - T3-matched: clears the building's production
 * word and re-runs the type's production callback with the "pay resources"
 * flag (0x51120) switched off, so the restart does not charge again.  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned short pay_resources;            /* 0x51120 */
extern void (*unit_type_callback[])(Unit *);    /* 0x510d8, [type] */

/* @0x11990 */
void RestartProduction(Unit *u)
{
    pay_resources = 0;
    u->word4a = 0;
    unit_type_callback[u->type](u);
    pay_resources = 1;
}
