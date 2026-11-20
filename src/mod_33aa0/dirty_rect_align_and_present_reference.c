/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -of+ -zp2 */
#include "mod_33aa0_c.h"

extern short dirty_x1;
extern short dirty_x2;
extern short dirty_w;
extern void VidPresentRect(void);

void DirtyRectAlignAndPresent(void)
{
    unsigned short a;

    a = (unsigned char)dirty_x1;
    a &= 3;
    if (a != 0) {
        dirty_w += a;
        dirty_x1 -= a;
    }
    a = (unsigned char)dirty_w;
    a &= 3;
    if (a != 0) {
        dirty_w += 4 - a;
    }
    dirty_x2 = dirty_x1 + dirty_w - 1;
    VidPresentRect();
}
