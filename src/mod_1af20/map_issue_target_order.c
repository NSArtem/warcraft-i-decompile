/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_1af20.h"

extern void GameScreenInputReset(unsigned char cursor); /* 0x1b4bc: eax = 0. */
extern void IssueOrderAt(short x, short y, Unit *target); /* 0x1b4d2: x/y/target in eax/edx/ebx. */

void MapIssueTargetOrder(void *evt)
{
    unsigned char *event = evt;
    short x;
    short y;

    x = (short)(((*(long *)(event + 2) >> 16) - 0x48) >> 4);
    y = (short)(((*(long *)(event + 4) >> 16) - 0xc) >> 4);
    x = (short)(x + map_scroll_x);
    y = (short)(y + map_scroll_y);
    GameScreenInputReset(0);
    IssueOrderAt(x, y, map_order_target);
}
