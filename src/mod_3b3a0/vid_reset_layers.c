/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_3b3a0.h"

extern short dirty_x1;
extern short dirty_y1;
extern short dirty_x2;
extern short dirty_y2;
extern short dirty_w;
extern short dirty_h;
extern char layers[];
extern void *memset(void *s, int c, unsigned n);

/* @0x3b3a0 */
void VidResetLayers(void)
{
    dirty_x1 = 0x7fff;
    dirty_y1 = 0x7fff;
    dirty_x2 = -0x8000;
    dirty_y2 = -0x8000;
    dirty_w = 0;
    dirty_h = 0;
    memset(layers, 0, 0x240);
}
