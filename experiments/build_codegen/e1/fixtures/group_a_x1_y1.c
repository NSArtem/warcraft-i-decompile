#include "mod_16390.h"

int DialogItemHitTest(Dialog *d, DialogItem *item)
{
    short x1, y1, right, bottom;
    x1 = layers[d->layer].x;
    x1 += item->x;
    y1 = layers[d->layer].y;
    y1 += item->y;
    right = x1 + item->art->w - 1;
    bottom = y1 + item->art->h - 1;
    if (x1 <= ui_mouse_x && right >= ui_mouse_x &&
        y1 <= ui_mouse_y && bottom >= ui_mouse_y)
        return 1;
    return 0;
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
