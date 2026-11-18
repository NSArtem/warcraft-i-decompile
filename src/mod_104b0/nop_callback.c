/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * NopCallback (0x106e8) - the empty callback that fills the unit-type
 * callback slots which have no behaviour (table at 0x510d8, index 0, and
 * 0x510c8).  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

/* @0x106e8 */
void NopCallback(void)
{
}
