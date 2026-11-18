/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * TrainWorkers (0x118a0): the town-hall production callback - train a worker
 * (types 2/3) while the per-player worker cap allows it.  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned short dat_5009a[];             /* 0x5009a worker cap */
extern unsigned short player_worker_count[];   /* 0x58dd8 */

extern void UnitStartTraining(Unit *u, unsigned char type);    /* 0x115f4 */

/* @0x118a0 */
void TrainWorkers(Unit *u)
{
    if (dat_5009a[u->owner] <= player_worker_count[u->owner])
        return;
    UnitStartTraining(u, (u->type - 0x20) & 1 ? 3 : 2);
}
