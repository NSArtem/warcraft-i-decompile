/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * Module mod_33a30 (0x33a30..0x33aa0), video library, "DBG" style. */
#include "graphics.h"

/* @0x33a30 */
void DirtyRectAddBox(short x1, short y1, short x2, short y2)
{
    if (x1 < dirty_x1) dirty_x1 = x1;
    if (y1 < dirty_y1) dirty_y1 = y1;
    if (x2 > dirty_x2) dirty_x2 = x2;
    if (y2 > dirty_y2) dirty_y2 = y2;
    dirty_w = dirty_x2 - dirty_x1 + 1;
    dirty_h = dirty_y2 - dirty_y1 + 1;
}
