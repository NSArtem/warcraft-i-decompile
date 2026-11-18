/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_328c0 (0x328c0..0x32940), DBG style. */
#include "graphics.h"

/* @0x328c0 */
void DirtyRectUnion(const short *r)
{
    if (r[0] < dirty_x1) dirty_x1 = r[0];
    if (r[1] < dirty_y1) dirty_y1 = r[1];
    if (r[2] > dirty_x2) dirty_x2 = r[2];
    if (r[3] > dirty_y2) dirty_y2 = r[3];
    dirty_w = dirty_x2 - dirty_x1 + 1;
    dirty_h = dirty_y2 - dirty_y1 + 1;
}
