/* codegen-compiler: 10.0a */
#include "mod_25820.h"

/* 0x2582e decrements the timer; 0x25965 writes it back. */
void MapScrollAddInputDeltas(short *dx, short *dy)
{
    register short countdown = key_scroll_countdown;
    unsigned int index;
    short reload;
    unsigned short phase;
    long delta;

    if (--countdown == 0) {
        index = opt_key_scroll;
        reload = key_scroll_repeat_delays[index];
        countdown = reload;
        if (scroll_alt_key_down || scroll_key_down_left || scroll_key_down || scroll_key_down_right)
            ++*dy;
        if (scroll_alt_key_up || scroll_key_up_left || scroll_key_up || scroll_key_up_right)
            --*dy;
        if (scroll_alt_key_right || scroll_key_down_right || scroll_key_right || scroll_key_up_right)
            ++*dx;
        if (scroll_alt_key_left || scroll_key_down_left || scroll_key_left || scroll_key_up_left)
            --*dx;

        phase = (mouse_position_scroll_phase == 0);
        mouse_position_scroll_phase = phase;
        if (!ui_input_locked && phase && mouse_position_scroll_key) {
            delta = ((*(long *)&ui_mouse_x_read_prefix >> 16) - 192L) / 16L;
            *dx = (short)((long)*dx + delta);
            delta = ((*(long *)&ui_mouse_x >> 16) - 100L) / 16L;
            *dy = (short)((long)*dy + delta);
        }
    }
    key_scroll_countdown = countdown;
}
