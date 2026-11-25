#include "mod_16390.h"

int DialogItemHitTest(Dialog *d, DialogItem *item)
{
    Layer *layer = &layers[d->layer];
    short x = layer->x + item->x;
    short y = layer->y + item->y;
    short right, bottom;
    right = x + item->art->w - 1;
    bottom = y + item->art->h - 1;
    if (x > ui_mouse_x || right < ui_mouse_x ||
        y > ui_mouse_y || bottom < ui_mouse_y)
        return 0;
    return 1;
}

void DialogHighlightOn(void)
{
    if (dialog_sounds_loaded != 0)
        SndPlay(0);
}

void DialogHighlightOff(void)
{
    if (dialog_sounds_loaded != 0)
        SndPlay(0);
}
