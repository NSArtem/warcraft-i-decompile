/* codegen-compiler: 10.0a */
/* mod_1b800.  0x1b9b8 (DB placeholder fn_1b9b8, owned by mod_20c30.toml): the
 * 'order acknowledged' voice.  A NULL unit or a player unit gets one of four
 * voices (ids 12..15); catapults and buildings get id 0x21.  Called by
 * PlaceBoxCreateBuilding and (as a tail jump) IssueOrderAt.  See
 * docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1b9b8 */
void fn_1b9b8(Unit *u)
{
    unsigned short id = 0xc;

    if (u != 0) {
        if (u->owner != 0)
            return;
        if (u->type == 4 || u->type == 5 || u->type >= 0x13)
            id = 0x21;
    }
    if (id == 0xc)
        id += rand() % 4;
    SndEvent(id, 0);
}
