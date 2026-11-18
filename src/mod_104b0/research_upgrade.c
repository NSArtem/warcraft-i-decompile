/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * ResearchUpgrade (0x118e0): the common body of the three research command
 * callbacks - refuse while the level cell is already marked (bit 0x80),
 * start the research while the level is below the cap, otherwise remember
 * the "at cap" word.  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern void UnitStartResearch(Unit *u, unsigned char row);     /* 0x11538 */

/* @0x118e0 */
void ResearchUpgrade(Unit *u, unsigned char row, unsigned char *level, int cap)
{
    unsigned lvl = *level;

    if ((lvl & 0x80) != 0)
        return;
    if (lvl < (unsigned) cap) {
        UnitStartResearch(u, row);
        return;
    }
    u->word4a = 0xffff;
}
