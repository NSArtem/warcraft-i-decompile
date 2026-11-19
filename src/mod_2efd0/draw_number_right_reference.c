/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* DrawNumberRight (0x2f878): draw a score number right-aligned at x. */
#include "mod_2efd0.h"

/* @0x2f878 */
void DrawNumberRight(short x, short y, long value)
{
    char text[0xa0];                 /* [0..0x50) digits, [0x50..) formatted */
    int w;

    FormatNumber(text, value, text + 0x50);
    w = TextWidth(cur_font, text + 0x50);
    DrawText(x - w, y, text + 0x50);
}
