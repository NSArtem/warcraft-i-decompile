/* codegen-compiler: 10.0a */
#include "mod_16390.h"

void ListSelectAtMouse(Dialog *d, DialogItem *item)
{
    unsigned short y = d->y + item->y + 3;
    unsigned short rows = ((Font *)default_font)->rows;
    unsigned short bottom = y + rows - 1;
    void **texts = item->text;
    unsigned short my = ui_mouse_y;
    int i = 0;

    if (texts[0] == 0)
        return;
    while (texts[i] != (void *)-1) {
        if (my >= y && my <= bottom) {
            d->params[item->id] = i;
            ListDraw(d, item);
            return;
        }
        y += rows;
        bottom += rows;
        i++;
    }
}
