/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x16520 */
void DialogDrawItems(Dialog *d)
{
    DialogItem *it = d->items;
    const char *s;
    unsigned short tw;

    while ((short)it->type != -1) {
        switch (it->type) {
        case 0:
        case 6:
        case 7:
        case 10:
            BitmapBlitTransparentAll(I16(&it->x), I16(&it->y), it->art);
            tw = (unsigned short)TextWidth(default_font, (const char *)it->text);
            DrawText((short)(it->x + (short)it->art->w / 2 - tw / 2), (short)(it->y + 3), (const char *)it->text);
            break;
        case 9:
            BitmapBlitTransparentAll(I16(&it->x), I16(&it->y), it->art);
            DrawText((short)(it->x + 10), (short)(it->y + 3), (const char *)it->text);
            break;
        case 1:
        case 2:
            BitmapBlitTransparentAll(I16(&it->x), I16(&it->y), it->art);
            break;
        case 3:
            s = ListSelectedText(d, it);
            tw = (unsigned short)TextWidth(default_font, s);
            DrawText((short)(it->x - tw / 2), I16(&it->y), s);
            break;
        case 8:
        case 11:
            DrawText(I16(&it->x), I16(&it->y), (const char *)it->text);
            break;
        case 5:
            BitmapBlitTransparentAll(I16(&it->x), I16(&it->y), it->art);
            ListDraw(d, it);
            break;
        }
        it++;
    }
}
