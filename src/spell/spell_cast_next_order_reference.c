/* codegen-compiler: 10.0a */
#include "spell.h"

extern union { unsigned long w; unsigned char b[4]; } cheat_flags; /* 0x51214 */
extern void UnitSetNextOrder(void *u, unsigned char order);        /* 0x2eeac */

/* @0x27adc */
void SpellCastNextOrder(struct Unit *u)
{
    unsigned char *p = (unsigned char *)u;
    short r;

    if (cheat_flags.w & 0x8) {
        p[0x1a] = 0xff;
    }
    r = (short)spell_handler_table[p[0x1f]](u, 1);
    if (p[0x1f] != 0x1a) {
        UnitSetNextOrder(u, 2);
    }
}
