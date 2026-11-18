/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * ResearchRangedUpgrade (0x11910): the "research ranged weapons" command
 * callback (player_upgrade row 0).  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_50008[];              /* 0x50008 upgrade row 0 */
extern void ResearchUpgrade(Unit *u, unsigned char row, unsigned char *level, int cap); /* 0x118e0 */

/* @0x11910 */
void ResearchRangedUpgrade(Unit *u)
{
    ResearchUpgrade(u, 0, &dat_50008[u->owner], 2);
}
