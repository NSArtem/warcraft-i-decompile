/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for 0x2905c StatusPanelShow (STATUS.C), the panel's opener.  One
 * function per file so every callee is an external symbol (the T4 difftest
 * stubs SetCursor and StatusPanelPressUpdate). */
#include "status.h"

/* The map view's fourth callback slot (0x59424), cleared when the panel
 * opens; it is published by the UI event layer (mod_16390, 0x18458/0x18470)
 * and has no symbol-database entry yet. */
extern void (*status_event_callback)(void);

/* 0x2905c - install the mouse and frame callbacks, clear the 0x59424 slot,
 * hide the cursor, show the panel and arm the focused button from the mouse
 * point: status_pressed becomes 1 when the point is OUTSIDE the button rect
 * (0x290b0-0x290e4 jump to `mov eax,1` on any of the four tests), so the first
 * update always draws.
 * Does nothing while the panel is locked or no button is focused. */
void StatusPanelShow(const void *pt)
{
    const short *p;
    const Rect *r;

    if (status_lock)
        return;
    if (status_button == 0)
        return;
    status_frame_callback = (void (*)(void))StatusPanelClick;
    status_click_callback = (void (*)(void))StatusPanelClick;
    status_mouse_callback = (void (*)(void *))StatusPanelPressUpdate;
    status_event_callback = 0;              /* 0x59424 (0x2909a) */
    SetCursor(0);
    status_visible = 1;
    p = pt;
    r = status_button_rect;
    status_pressed = (p[2] < r->x1 || p[2] > r->x2 || p[3] < r->y1 || p[3] > r->y2);
    StatusPanelPressUpdate(pt);
}
