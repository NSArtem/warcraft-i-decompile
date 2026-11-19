/* codegen-compiler: 10.0a */
/* mod_1b800.  SndBuildingDestroyed 0x1b92c: one of the three 'building
 * destroyed' sounds.  Called by UnitRemove 0x2e14c.  See
 * docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1b92c */
void SndBuildingDestroyed(void)
{
    SndEvent((unsigned short)(0x18 + rand() % 3), 0);
}
