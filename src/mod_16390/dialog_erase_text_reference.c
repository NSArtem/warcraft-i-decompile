/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x1718c */
void DialogEraseText(Dialog *d)
{
    DialogItem *it;
    Rect r;
    const char *s;
    int w;

    for (it = d->items; it->type != (unsigned short)-1; it++) {
        if (it->type == 3 || it->type == 8 || it->type == 11) {
            if (it->type == 3)
                s = ListSelectedText(d, it);
            else
                s = (const char *)it->text;
            w = TextWidth(default_font, s);
            r.x = it->x;
            if (it->type == 3)
                r.x = I16(&r.x) - (int)(unsigned short)w / 2;
            r.y = it->y;
            r.right = r.x + w - 1;
            r.bottom = r.y + ((Font *)default_font)->rows - 1;
            r.w = r.right - r.x + 1;
            r.h = r.bottom - r.y + 1;
            draw_color = 0;
            FillRect(I16(&r.x), I16(&r.y), r.w, r.h);
            r.x += d->x;
            r.right += d->x;
            r.y += d->y;
            r.bottom += d->y;
            r.w = r.right - r.x + 1;
            r.h = r.bottom - r.y + 1;
            DirtyRectUnion((const short *)&r);
        }
    }
}
