/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * ResearchArmourUpgrade (0x11950): the blacksmith research command - raise
 * the melee weapon row (1) or the armour row (9), whichever is lower.
 * See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned char dat_5000d[];              /* 0x5000d upgrade row 1 */
extern unsigned char dat_50035[];              /* 0x50035 upgrade row 9 */
extern void ResearchUpgrade(Unit *u, unsigned char row, unsigned char *level, int cap); /* 0x118e0 */

/* @0x11950 */
void ResearchArmourUpgrade(Unit *u)
{
    unsigned char *cell;
    int row;

    if (dat_50035[u->owner] < dat_5000d[u->owner]) {
        row = 9;
        cell = &dat_50035[u->owner];
    } else {
        row = 1;
        cell = &dat_5000d[u->owner];
    }
    ResearchUpgrade(u, row, cell, 2);
}
