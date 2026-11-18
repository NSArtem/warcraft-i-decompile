/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (0x13f60..0x16390): the unit order dispatch (DISPATCH.C) -
 * the update handler of order 9.  See docs/subsystems/mod_13f60.md. */
#include "mod_13f60.h"

/* @0x141d0: order 9, entry 9 of order_update_table 0x5158c.  Drops the attack
 * target (+0x3a) and freezes the animation timer, and never finishes. */
int OrderUpdateHold(OrderUnit *u)
{
    u->target = 0;
    u->anim_timer = 0xff;
    return 0;
}
