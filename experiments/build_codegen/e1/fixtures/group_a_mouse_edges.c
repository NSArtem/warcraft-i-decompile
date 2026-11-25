#include "mod_16390.h"

int DialogItemHitTest(Dialog *d, DialogItem *item)
{
    short left, top, right_edge, bottom_edge;
    left = layers[d->layer].x;
    left += item->x;
    top = layers[d->layer].y;
    top += item->y;
    right_edge = left + item->art->w - 1;
    bottom_edge = top + item->art->h - 1;
    if (left <= ui_mouse_x && right_edge >= ui_mouse_x &&
        top <= ui_mouse_y && bottom_edge >= ui_mouse_y)
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
