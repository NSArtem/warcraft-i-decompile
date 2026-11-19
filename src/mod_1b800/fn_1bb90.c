/* codegen-compiler: 10.0a */
/* mod_1b800.  0x1bb90 (DB placeholder fn_1bb90, owned by mod_104b0.toml): arm
 * the unit's attack sound (+9) from the per-type table; the sword hit (0x23)
 * has three variants.  Called by the attack orders 0x113ce/0x1142e/0x114cc.
 * See docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1bb90 */
void fn_1bb90(Unit *u)
{
    unsigned short s = unit_attack_sound[u->type];

    if (s == 0x23)
        s += rand() % 3;
    u->sound = (unsigned char)s;
}
