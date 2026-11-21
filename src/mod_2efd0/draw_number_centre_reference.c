/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* DrawNumberCentre (0x2f8bc): draw a score number centred on x. */
#include "mod_2efd0.h"

/* @0x2f8bc */
void DrawNumberCentre(short x, short y, long value)
{
    char text[0xa0];
    int w;

    FormatNumber(text, value, text + 0x50);
    w = TextWidth(cur_font, text + 0x50);
    DrawText((short)(x - (short)w / 2), y, text + 0x50);
}
