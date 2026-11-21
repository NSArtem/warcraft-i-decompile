/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x16d5c */
void DialogDrawItemState(Dialog *d, DialogItem *item, int pressed, int focus)
{
    short r[4];
    short tw;
    short x;
    unsigned short t;

    BitmapBlitTransparentAll(item->x, item->y, (pressed != 0) ? item->art_pressed : item->art);
    t = item->type;
    if (t == 0 || t == 6 || t == 7 || t == 9 || t == 10) {
        if (focus != 0) {
            TextSetEscapeColors(0xf6, 0xf6);
            TextSetColorBase(0xf6);
        } else {
            TextSetEscapeColors(0xf6, 0xf3);
            TextSetColorBase(0xf3);
        }
        tw = (short)TextWidth(default_font, (const char *)item->text);
        if (item->type == 9) {
            x = item->x + 10;
        } else {
            x = item->x + item->art->w / 2 - (unsigned short)tw / 2;
        }
        DrawText(x, (short)(item->y + 3), (const char *)item->text);
    }
    r[0] = layers[d->layer].x + item->x;
    r[1] = layers[d->layer].y + item->y;
    r[2] = r[0] + item->art->w - 1;
    r[3] = r[1] + item->art->h - 1;
    DirtyRectUnion(r);
}
