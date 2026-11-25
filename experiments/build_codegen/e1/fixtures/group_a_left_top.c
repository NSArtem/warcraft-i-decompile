#include "mod_16390.h"

int DialogItemHitTest(Dialog *d, DialogItem *item)
{
    short left, top, right, bottom;
    left = layers[d->layer].x;
    left += item->x;
    top = layers[d->layer].y;
    top += item->y;
    right = left + item->art->w - 1;
    bottom = top + item->art->h - 1;
    if (left <= ui_mouse_x && right >= ui_mouse_x &&
        top <= ui_mouse_y && bottom >= ui_mouse_y)
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
