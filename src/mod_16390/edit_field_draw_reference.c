/* codegen-compiler: 10.0a */
#include "mod_16390.h"

void VLine(short x, unsigned short y, unsigned short len);

/* @0x174c0 */
void EditFieldDraw(Rect r, short caret)
{
    int tw;

    draw_color = 0;
    FillRect(I16(&r.x), I16(&r.y), r.w, r.h);
    TextSetColorBase(0xf3);
    DrawText((short)(r.x + 3), I16(&r.y), edit_buffer);
    if (caret != 0) {
        draw_color = 0xf6;
        tw = TextWidth(cur_font, edit_buffer);
        VLine((short)(tw + (r.x + 3) - TextWidth(cur_font, edit_buffer + edit_cursor) - 1), I16(&r.y), (unsigned short)(r.h - 2));
    }
    DirtyRectUnion((const short *)&r);
}
