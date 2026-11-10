/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_2c4e0 (PATH.C, 0x2c4e0..0x2ced0), game code, "OPT" style.
 * One function (0x2cebc); see docs/subsystems/game_2c4e0.md. */
#include "game_2c4e0.h"

/* @0x2cebc */
void UnitResetPath(Unit *u)
{
    u->path_idx = 20;
}
