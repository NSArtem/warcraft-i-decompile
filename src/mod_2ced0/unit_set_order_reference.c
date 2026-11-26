/* codegen-compiler: 10.0a */
#include "mod_2ced0_c.h"

extern unsigned char order_sound[32];
extern void UnitStartAnim(Unit *u, unsigned sound);

/* @0x2ee50 */
void UnitSetOrder(Unit *u, unsigned char order)
{
    if ((u->flags & 0x207) == 0) {
        u->pad1f[1] = 0x1f;
        u->pad1f[2] = 0x1f;
        u->pad1f[0] = order;
        if ((order & 0xff) == 2 && u->b1b <= 0x1f) {
            u->u52.p = 0;
        }
        UnitStartAnim(u, order_sound[u->pad1f[0]]);
        *((unsigned char *)u + 0x11) &= 0x3f;
    }
}
