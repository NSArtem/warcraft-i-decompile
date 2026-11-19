/* codegen-compiler: 10.0a */
/* mod_1b800.  UnitSetWorkSound 0x1bc0c: arm one of four sounds in the unit's
 * pending-sound byte (+9), which the animation opcode 0x10457 plays.  Called by
 * fn_1cd90.  See docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1bc0c */
void UnitSetWorkSound(Unit *u)
{
    u->sound = 0x1c + rand() % 4;
}
