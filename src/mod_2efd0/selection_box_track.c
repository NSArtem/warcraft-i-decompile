/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* SelectionBoxTrack (0x2f0c8): the mouse-move half of the drag rectangle -
 * min/max the press anchor against the current Event position, derive the
 * box size and make it visible.  T3; -oa stores the bx copy instead of
 * re-reading the event (found by wc1.t3_audit). */
#include "mod_2efd0.h"

/* @0x2f0c8 */
void SelectionBoxTrack(Event *ev)
{
    short a;

    a = selection_box.anchor_x;
    if (a <= (short)ev->x) {
        selection_box.min_x = a;
        selection_box.max_x = ev->x;
    } else {
        selection_box.min_x = ev->x;
        selection_box.max_x = a;
    }
    a = selection_box.anchor_y;
    if (a <= (short)ev->y) {
        selection_box.min_y = a;
        selection_box.max_y = ev->y;
    } else {
        selection_box.min_y = ev->y;
        selection_box.max_y = a;
    }
    selection_box.w = selection_box.max_x - selection_box.min_x + 1;
    selection_box.h = selection_box.max_y - selection_box.min_y + 1;
    selection_box.visible = 1;
}
