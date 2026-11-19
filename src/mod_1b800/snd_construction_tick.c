/* codegen-compiler: 10.0a */
/* mod_1b800.  SndConstructionTick 0x1bc2c: the occasional construction noise
 * (about 2.3 % of the ticks).  Called by UnitStartDeath 0x2d0e0.  See
 * docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1bc2c */
void SndConstructionTick(Unit *u)
{
    if (rand() <= 0x300)
        SndEvent(2, u);
}
