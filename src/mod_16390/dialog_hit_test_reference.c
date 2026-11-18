/* codegen-compiler: 10.0a */
/* 0x16cc8: is the mouse inside the item? (the highlight helpers 0x16d34 and
 * 0x16d48 reuse this function's epilogue in the original, so they live in
 * this file.) */
#include "mod_16390.h"

int DialogItemHitTest(Dialog *d, DialogItem *item)
{
    short x = layers[d->layer].x + item->x;
    short y = layers[d->layer].y + item->y;
    short right = x + item->art->w - 1;
    short bottom = y + item->art->h - 1;

    if (x > ui_mouse_x)
        return 0;
    if (right < ui_mouse_x)
        return 0;
    if (y > ui_mouse_y)
        return 0;
    if (bottom < ui_mouse_y)
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
