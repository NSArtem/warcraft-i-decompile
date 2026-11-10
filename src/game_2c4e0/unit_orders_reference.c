/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_2ced0 (UNIT.C, 0x2ced0..0x2efd0), game code, "OPT" style.
 * Reference C for UnitSetNextOrder (0x2eeac).  The logic is the same as the
 * matching 0x2eed4 (unit_orders.c); this spelling is only three bytes off
 * (OW2 uses dh for the order byte where the original uses bl), so the
 * function is a near miss (not built). */
#include "game_2c4e0.h"

/* @0x2eeac */
void UnitSetNextOrder(Unit *u, unsigned char order)
{
    unsigned char g;
    unsigned f;
    f = u->flags.w & 0x207;
    if (f == 0) {
        g = u->order;
        if (g != 0xc) {
            u->order_next2 = 0x1f;
            u->order_next = order;
            u->flags.b.hi &= 0x7f;
        }
    }
}
