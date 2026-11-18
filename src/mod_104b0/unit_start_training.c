/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * UnitStartTraining (0x115f4): a building starts training one unit of the
 * given type: pay for it, set the build timer and switch to the training
 * order (0x0f).  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern CheatFlags cheat_flags;                 /* 0x51214 */
extern unsigned short pay_resources;           /* 0x51120 */
extern unsigned char unit_train_time[];        /* 0x51a14 */
extern unsigned short training_count[];        /* 0x50d84 */

extern int fn_20d74(unsigned short player, int pay, unsigned char type); /* 0x20d74 */
extern void fn_19f70(const char *msg, unsigned n);             /* 0x19f70 */
extern void UnitSetNextOrder(Unit *u, unsigned char order);    /* 0x2eeac */

/* @0x115f4 */
void UnitStartTraining(Unit *u, unsigned char type)
{
    if ((u->flags2 & 0x10) != 0)
        return;
    if (pay_resources != 0) {
        const char *err = (const char *) fn_20d74(u->owner, 1, type);

        if (err != 0) {
            if (u->owner != 0)
                return;
            fn_19f70(err, 0x24);
            return;
        }
    }
    u->build_type = type;
    u->build_cost = 0;
    u->build_time = unit_train_time[type];
    if (cheat_flags.f.fast)
        u->build_time >>= 2;
    u->energy = 1;
    u->b40 = 1;
    u->b3f = 2;
    u->flags2 |= 0x10;
    if (type != 0x35)
        training_count[u->owner]++;
    UnitSetNextOrder(u, 0xf);
}
