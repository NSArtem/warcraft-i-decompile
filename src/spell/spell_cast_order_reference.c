/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
#include "spell.h"

extern union { unsigned long w; unsigned char b[4]; } cheat_flags;
extern void UnitSetOrder(struct Unit *u, unsigned char order);

/* @0x27aa4 */
void SpellCastOrder(struct Unit *u)
{
    short r;

    if (cheat_flags.w & 8) {
        ((unsigned char *)u)[0x1a] = 0xff;
    }
    r = (short)spell_handler_table[((unsigned char *)u)[0x1f]](u, 0);
    if (r == 0) {
        UnitSetOrder(u, 2);
    }
}
