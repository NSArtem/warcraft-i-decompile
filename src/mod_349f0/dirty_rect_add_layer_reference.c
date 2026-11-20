/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 */
#include "mod_349f0_c.h"

extern short dat_5aa92[];
extern short dirty_x1;
extern short dirty_y1;
extern short dirty_x2;
extern short dirty_y2;
extern short dirty_w;
extern short dirty_h;

/* @0x349f0 */
void DirtyRectAddLayer(unsigned char id)
{
    if (dat_5aa92[id * 9] < dirty_x1) {
        dirty_x1 = dat_5aa92[id * 9];
    }
    if (dat_5aa92[id * 9 + 1] < dirty_y1) {
        dirty_y1 = dat_5aa92[id * 9 + 1];
    }
    if ((short)(dat_5aa92[id * 9] + dat_5aa92[id * 9 + 2] - 1) > dirty_x2) {
        dirty_x2 = dat_5aa92[id * 9] + dat_5aa92[id * 9 + 2] - 1;
    }
    if ((short)(dat_5aa92[id * 9 + 1] + dat_5aa92[id * 9 + 3] - 1) > dirty_y2) {
        dirty_y2 = dat_5aa92[id * 9 + 1] + dat_5aa92[id * 9 + 3] - 1;
    }
    dirty_w = dirty_x2 - dirty_x1 + 1;
    dirty_h = dirty_y2 - dirty_y1 + 1;
}
