/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Drawing primitives of the video library (see analysis/symbols/graphics.toml).
 * Reference C: both functions are T3 near misses (VLine with 10.0a spills the
 * width where the original spills y; HLine differs in the prologue), so the
 * behaviour is difftested against the original in tests/test_graphics_lib.py
 * (VLine) and tests/test_graphics_text.py (both, against a Python model). */
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
