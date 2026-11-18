/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x28170 - "cancel unit training" (0x54464/0x544d8): busy, nothing built yet
 * (unit+0x46 == 0) and the produced type is not the construction menu id 0x35. */
#include "status.h"

unsigned short CanCancelTraining(short is_unit)
{
    Unit *u = SelectionFirst(0x63);   /* the original passes a constant here */
    unsigned long busy;
    unsigned char prod;

    busy = u->sflags & 0x10;
    if (busy != 0) {
        if (u->work.progress == 0) {
            prod = u->prod_type;
            if (prod != 0x35)
                return 1;
        }
    }
    return 0;
}
