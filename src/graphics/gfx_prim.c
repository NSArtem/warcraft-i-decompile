/* Drawing primitives of the video library (see analysis/symbols/graphics.toml).
 * NOT a match: the original (Watcom 10.x, frame-pointer style prologue) differs from OW2 -s -ot/-od
 * output; this is reference C only, behaviour is checked by tests/test_graphics_text.py. */
#include <string.h>
#include "graphics.h"

void HLine(short x, unsigned short y, unsigned short len)
{
    unsigned char *p = cur_bitmap->data + cur_bitmap->w * y + x;
    unsigned short i;
    for (i = 0; i < len; i++)
        *p++ = draw_color;
}

void VLine(short x, unsigned short y, unsigned short len)
{
    unsigned char *p = cur_bitmap->data + cur_bitmap->w * y + x;
    unsigned short i;
    for (i = 0; i < len; i++) {
        *p = draw_color;
        p += cur_bitmap->w;
    }
}
