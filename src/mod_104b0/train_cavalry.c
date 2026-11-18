/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * TrainCavalry (0x117f0): the stable/kennel production callback - train the
 * race's mounted unit (types 0xc/0xd) while the per-player cap allows it.
 * See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned short player_unit_cap[];       /* 0x58dec */
extern unsigned short player_unit_count[];     /* 0x58dc4 */

extern void UnitStartTraining(Unit *u, unsigned char type);    /* 0x115f4 */

/* @0x117f0 */
void TrainCavalry(Unit *u)
{
    int cap = player_unit_cap[u->owner];

    if (cap > 4)
        cap = 4;
    if (cap < player_unit_count[u->owner])
        return;
    UnitStartTraining(u, (u->type - 0x20) & 1 ? 0xd : 0xc);
}
