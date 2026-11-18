/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * AnimEndDispatch (0x1077c): the "animation script finished" opcode of the
 * unit animation interpreter.  Clears the animation timer and dispatches the
 * unit's order handler through order_handler_table[u->order].  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern void (*order_handler_table[])(Unit *);   /* 0x510a0 */

/* @0x1077c */
void AnimEndDispatch(Unit *u)
{
    unsigned f = u->flags.w & 0x4000;

    if (f == 0) {
        u->timer36 = 0;
        order_handler_table[u->order](u);
    }
}
