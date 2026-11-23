/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for 0x28600 StatusPanelClick (STATUS.C), the panel's frame/click
 * callback.  One function per file so the other callbacks are external
 * symbols (the T4 difftest stubs them and their callees). */
#include "status.h"

/* 0x28600 - update the armed button from the mouse point, restore the map
 * input, hide the panel, and when a button is armed run its action - the order
 * layer command stored in the button record (b->action(b->arg)). */
void StatusPanelClick(const void *pt)
{
    StatusPanelPressUpdate(pt);
    GameScreenInputInit();
    status_visible = 0;
    if (!status_pressed)
        return;
    ButtonDraw(status_button, 0);
    DirtyRectUnion(status_button_rect);
    ScreenUpdate();
    status_button->action(status_button->arg);
}
