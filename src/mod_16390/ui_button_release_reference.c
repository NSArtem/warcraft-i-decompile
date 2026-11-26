/* codegen-compiler: 10.0a */
/* 0x183e8: event table indexes 5 and 7 - a mouse button came up. */
#include "mod_16390.h"

void UiButtonRelease(Event *ev)
{
    int sub = ev->sub;

    if (sub == 7) {
        if ((unsigned char)ui_button_bits & 2) {
            (*(unsigned char *)&ui_button_bits) &= ~2;
            if (status_click_callback != 0)
                status_click_callback();
        }
    } else if (sub == 5) {
        if ((unsigned char)ui_button_bits & 1) {
            (*(unsigned char *)&ui_button_bits) &= ~1;
            if (status_frame_callback != 0)
                status_frame_callback();
        }
    }
    DemoIdleTimerReset();
}
