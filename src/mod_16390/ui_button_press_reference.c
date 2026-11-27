/* codegen-compiler: 10.0a */
/* 0x18398: event table indexes 4 and 6 - a mouse button went down.  A second
 * button is ignored while one is already held (ui_button_bits != 0). */
#include "mod_16390.h"

void UiButtonPress(Event *ev)
{
    int sub;

    if (ui_button_bits != 0)
        return;
    sub = ev->sub;
    if (sub == 6) {
        ui_button_bits |= 2;
        if (dialog_right_press != 0)
            dialog_right_press();
    } else if (sub == 4) {
        ui_button_bits |= 1;
        if (dialog_left_press != 0)
            dialog_left_press();
    }
    DemoIdleTimerReset();
}
