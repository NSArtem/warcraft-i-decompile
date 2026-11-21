/* codegen-compiler: 10.0a */
#include "mod_2ced0_c.h"

extern void UnitOrderTargetFinish(Unit *u);

/* @0x2e100 */
void UnitOrderTarget(Unit *u, short x, short y, Unit *target, void (*fn)(Unit *))
{
    if (u->pad1f[0] != 12 && u->pad1f[0] > 1) {
        ((unsigned char *)u)[0x11] = (unsigned char)((((unsigned char *)u)[0x11] | 0x40) & 0x7f);
        *((char *)u + 9) = 0;
        u->u52.p = target;
        if (target != 0) {
            *(long *)((char *)u + 0x4e) = *(long *)((char *)target + 0xa);
        } else {
            *(short *)((char *)u + 0x4e) = x;
            u->s50 = y;
        }
        fn(u);
        UnitOrderTargetFinish(u);
    }
}
