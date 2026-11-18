/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * UnitStartResearch (0x11538): a building starts an upgrade/spell research:
 * pay for it, mark the level cell as in progress, set the build timer and
 * switch the building to the research order (0x10).  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern CheatFlags cheat_flags;                 /* 0x51214 */
extern unsigned short pay_resources;           /* 0x51120 */
extern unsigned char research_time[];          /* 0x51876 */

extern int fn_20d14(unsigned short player, int pay, unsigned char row, void **cost); /* 0x20d14 */
extern unsigned short ResearchCost(unsigned short player, unsigned char row, void **level); /* 0x28c60 */
extern void fn_19f70(const char *msg, unsigned n);             /* 0x19f70 */
extern void UnitSetNextOrder(Unit *u, unsigned char order);    /* 0x2eeac */

/* @0x11538 */
void UnitStartResearch(Unit *u, unsigned char row)
{
    void *cell;

    if ((u->flags2 & 0x10) != 0)
        return;
    if (pay_resources != 0) {
        const char *err = (const char *) fn_20d14(u->owner, 1, row, &cell);

        if (err != 0) {
            if (u->owner != 0)
                return;
            fn_19f70(err, 0x24);
            return;
        }
    } else {
        ResearchCost(u->owner, row, &cell);
    }
    *(unsigned char *) cell |= 0x80;
    u->build_type = row;
    u->build_time = research_time[row];
    if (cheat_flags.f.fast)
        u->build_time >>= 2;
    u->build_cost = cell;
    u->energy = 1;
    u->b40 = 1;
    u->b3f = 2;
    u->flags2 |= 0x10;
    UnitSetNextOrder(u, 0x10);
}
