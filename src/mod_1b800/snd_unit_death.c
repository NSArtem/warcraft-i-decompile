/* codegen-compiler: 10.0a */
/* mod_1b800.  SndUnitDeath 0x1b954: the sound of a removed unit, by type.
 * Called by UnitRemove 0x2e14c.  See docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1b954 */
void SndUnitDeath(Unit *u)
{
    unsigned short id;

    if (u->type == 4 || u->type == 5)
        return;
    if (u->type >= 0x13 && u->type <= 0x1f) {
        if (u->type == 0x13)
            id = 0x17;
        else if (u->type == 0x19)
            id = 0x16;
        else if (u->type == 0x17)
            id = 0xb;
        else
            id = 0x2b;
    } else if ((u->type & 1) == 0) {
        id = 0x16;
    } else {
        id = 0x17;
    }
    SndEvent(id, u);
}
