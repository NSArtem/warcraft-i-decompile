/* codegen-compiler: 10.0a */
/* mod_1b800.  0x1bd04 (DB placeholder fn_1bd04, owned by mod_104b0.toml): the
 * 'under attack' voice for a player unit that is hit; the alert (ids 0x12/0x13)
 * repeats only after the 4000-tick cool-down of the surrounding units.  Called
 * by UnitRetaliate.  See docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

extern void UnitAlertSuppressArea(Unit *u);    /* 0x1bc60 */

/* @0x1bd04 */
void fn_1bd04(Unit *u)
{
    unsigned short id;
    Unit *w;

    if (u->owner == 0 && u->type < 0x13 && u->alert_timer == 0) {
        UnitAlertSuppressArea(u);
        w = 0;                  /* the NULL unit lives in a register in the original (ebx) */
        /* the original keeps the unit live in edx across this test; the always-true
         * `u != 0` reproduces its `xor eax,eax; mov al,[edx+0x1b]` reload (code generation only) */
        if (u->type >= 0x20 && u->type <= 0x32 && u != 0)
            id = 0x13;
        else
            id = 0x12;
        SndEvent(id, w);
    }
}
