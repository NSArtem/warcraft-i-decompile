/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* ButtonAvailable (0x28434), built from C: T3 under Watcom 10.0a.  Split out
 * of draw_reference.c (reference C under OW2); one function per object. */
#include "status.h"

/* 0x28434 - is this button usable for the displayed unit?  A live unit only
 * offers the arm/attack path (the original compares the predicate with the
 * shared `return 0` block at 0x28090, the cancel-construction gate); a busy
 * or dead unit only keeps the three cancel buttons; everything else asks the
 * button's own predicate with the argument "this is not a building". */
unsigned short ButtonAvailable(const CommandButton *b)
{
    if (!(status_unit->flags & 0x80))
        return b->available == SelectionIsWorkersFalse;
    if (status_unit->sflags & 0x10) {
        if (b->available != CanCancelTraining &&
            b->available != CanCancelUpgrade &&
            b->available != CanCancelConstruction)
            return 0;
    }
    return b->available(status_unit->type <= 0x1f);
}
