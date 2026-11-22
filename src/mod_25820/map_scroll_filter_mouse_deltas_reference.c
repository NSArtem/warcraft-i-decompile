/* codegen-compiler: 10.0a */
#include "mod_25820.h"

/* 0x25993 tests repeat before 0x259ad tests initial scrolling. */
void MapScrollFilterMouseDeltas(short *dx, short *dy)
{
    short countdown = mouse_scroll_countdown;
    unsigned int offset;

    if (countdown != 0) {
        *dx = 0;
        *dy = 0;
        --countdown;
    } else {
        offset = opt_mouse_scroll;
        offset += offset;
        if (mouse_scroll_repeat_enabled) {
            countdown = *(short *)((char *)mouse_scroll_repeat_delays + offset);
            mouse_scroll_countdown = countdown;
            return;
        }
        if (mouse_scroll_initial_enabled) {
            countdown = *(short *)((char *)mouse_scroll_initial_delays + offset);
            mouse_scroll_countdown = countdown;
            return;
        }
        *dx = countdown;
        *dy = countdown;
    }
    mouse_scroll_countdown = countdown;
}
