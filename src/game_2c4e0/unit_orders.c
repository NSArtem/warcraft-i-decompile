/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_2ced0 (UNIT.C, 0x2ced0..0x2efd0), game code, "OPT" style.
 * UnitSetNextOrders (0x2eed4) - T3-matched; see
 * docs/subsystems/game_2c4e0.md.  Reusing the mask local for the order check
 * reproduces the original's single register (and the `and ecx,0xffff`
 * zero-extension); the one-argument sibling 0x2eeac is reference C in
 * unit_orders_reference.c (OW2 picks ecx instead of ebx). */
#include "game_2c4e0.h"

/* @0x2eed4 */
void UnitSetNextOrders(Unit *u, unsigned char order, unsigned char order2)
{
    unsigned f = u->flags.w & 0x207;

    if (f == 0) {
        f = (unsigned char)u->order;
        if (f != 0xc) {
            u->order_next = order;
            u->order_next2 = order2;
            u->flags.b.hi &= 0x7f;
        }
    }
}
