/* codegen-compiler: 10.0a */
#include "mod_2ced0_c7.h"

extern void DrawListRemove(void *u);
extern unsigned char dat_5008c[5];

void UnitFinalizeGone(struct Unit *u)
{
    unsigned short flags;
    unsigned masked;
    int type;

    DrawListRemove(u);
    if (dat_5008c[u->owner] != 1)
        goto release_unit;
    flags = *(volatile unsigned short *)&u->flags;
    flags &= 0x0400;
    masked = (unsigned)flags & 0xffffU;
    if (masked == 0)
        goto release_unit;
    u->flags = 0x0200;
    type = u->type;
    if (type < 0x20 || type > 0x32)
        goto done;
    u->gone_timer = 0xff;
    return;

release_unit:
    u->owner = 4;
    u->flags = 1;
done:
    return;
}
