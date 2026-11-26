/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_110a0 (0x110a0..0x11530), the attack order handlers.
 * AttackFatalStub (0x1132c) is the slot of order 4 in order_update_table
 * 0x5158c: the pending attack command is always re-ordered to the target
 * orders 5..8, so the slot is a tag assertion that never returns. */
#include "war.h"

extern const char attack_fatal_tag[];   /* 0x569d4 "attack:1" */

/* @0x1132c */
int AttackFatalStub(void)
{
    FatalError(attack_fatal_tag);
    return 0;
}
