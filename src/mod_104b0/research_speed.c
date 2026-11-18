/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * ResearchSpeedUpgrade (0x11930): the "breed faster horses/wolves" command
 * callback (player_upgrade row 2, 0x50012).  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_50012[];              /* 0x50012 upgrade row 2 */
extern void ResearchUpgrade(Unit *u, unsigned char row, unsigned char *level, int cap); /* 0x118e0 */

/* @0x11930 */
void ResearchSpeedUpgrade(Unit *u)
{
    ResearchUpgrade(u, 2, &dat_50012[u->owner], 2);
}
