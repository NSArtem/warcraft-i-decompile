/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x28140 - "cancel upgrade" on the blacksmith card (0x54384/0x543fc): the
 * displayed unit is busy (unit+0x0e bit 0x10) and an upgrade is in progress
 * (unit+0x46 != 0). */
#include "status.h"

unsigned short CanCancelUpgrade(short is_unit)
{
    Unit *u = SelectionFirst(0x62);   /* the original passes a constant here */
    unsigned long busy;

    busy = u->sflags & 0x10;
    if (busy != 0) {
        if (u->work.progress != 0)
            return 1;
    }
    return 0;
}
