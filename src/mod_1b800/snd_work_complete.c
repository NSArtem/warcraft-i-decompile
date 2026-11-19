/* codegen-compiler: 10.0a */
/* mod_1b800.  SndWorkComplete 0x1bc48: 'work complete' for the player's own
 * finished construction.  Called by UnitStartDeath 0x2d0e0.  See
 * docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1bc48 */
void SndWorkComplete(Unit *u)
{
    if (u->owner == 0)
        SndEvent(0x10, 0);
}
