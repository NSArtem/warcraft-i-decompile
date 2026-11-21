/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x163c8 */
void ListDraw(Dialog *d, DialogItem *item)
{
    unsigned short rows = ((Font *)default_font)->rows;
    short idx = 0;
    short sel;
    short x, y, ty, w, h;
    char **p;
    DialogItem *it = d->items;

    while (it->type != 5) {
        if (it->type == 0xffff)
            return;
        it++;
    }
    sel = (short)d->params[it->id];
    x = it->x + 3;
    y = it->y + 3;
    ty = y;
    w = it->x + 3 + it->code - 1 - x + 1;
    h = rows;
    p = (char **)it->text;
    while ((long)*p != -1) {
        if (idx++ == sel)
            draw_color = 0xf6;
        else
            draw_color = 0xfb;
        FillRect(x, y, w, h);
        if (*p != 0) {
            TextSetColorBase(0xf3);
            DrawText((short)(it->x + 5), ty, *p);
        }
        y += rows;
        ty += rows;
        p++;
    }
    LayerInvalidate((unsigned char)d->layer);
}
