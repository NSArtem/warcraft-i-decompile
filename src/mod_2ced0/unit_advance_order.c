/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_2ced0_c.h"

extern int GameRandom(int n);
extern void UnitStartAnim(Unit *u, unsigned sound);
extern unsigned char order_sound[32];

/* @0x2edac */
unsigned short UnitAdvanceOrder(Unit *u, int use_arg)
{
    if ((u->flags & 0x207) != 0)
        return 0;
    if (u->pad1f[1] != 0x1f) {
        u->pad1f[0] = u->pad1f[1];
        u->pad1f[1] = 0x1f;
    } else {
        if ((short)use_arg == 0 || u->pad1f[2] == 0x1f)
            return 0;
        u->pad1f[0] = u->pad1f[2];
        u->pad1f[2] = 0x1f;
    }
    if (u->pad1f[0] == 2 && u->b1b <= 0x1f)
        u->u52.p = 0;
    UnitStartAnim(u, order_sound[u->pad1f[0]]);
    if ((u->flags & 0x8000) != 0)
        *((unsigned char *)u + 6) = (GameRandom(0xb) & 7) + 1;
    u->flags &= 0x3fff;
    return 1;
}
