/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x281ac - "cancel construction" (0x54478/0x544f0): busy, nothing built yet
 * (unit+0x46 == 0) and the produced type is the construction menu id 0x35. */
#include "status.h"

unsigned short CanCancelConstruction(short is_unit)
{
    Unit *u = SelectionFirst(0x63);   /* the original passes a constant here */
    unsigned long busy;
    unsigned char prod;

    busy = u->sflags & 0x10;
    if (busy != 0) {
        if (u->work.progress == 0) {
            prod = u->prod_type;
            if (prod == 0x35)
                return 1;
        }
    }
    return 0;
}
