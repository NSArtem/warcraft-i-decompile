/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for the panel's input side of STATUS.C: StatusPanelPressUpdate
 * 0x28580, StatusPanelClick 0x28600, StatusPanelShow 0x2905c and
 * StatusPanelHandleKey 0x29354.  The mouse callbacks are installed in the
 * 0x5940c/0x59414/0x5941c slots of the map view, which is how the panel
 * receives the mouse button and the frame callback while it is open. */
#include "status.h"

/* 0x28580 - the mouse handler: when the point is inside the focused button's
 * rect the button is armed (drawn pressed); leaving it disarms it.  Both
 * states mark the button rect dirty. */
void StatusPanelPressUpdate(const void *pt)
{
    const short *p = pt;
    const Rect *r = status_button_rect;
    short inside;

    cur_bitmap = &status_panel_bm;
    inside = (p[2] >= r->x1 && p[2] <= r->x2 && p[3] >= r->y1 && p[3] <= r->y2);
    if (inside) {
        if (status_pressed)
            return;
        status_pressed = 1;
        ButtonDraw(status_button, 1);
    } else {
        if (!status_pressed)
            return;
        status_pressed = 0;
        ButtonDraw(status_button, 0);
    }
    DirtyRectUnion(r);
}

/* 0x28600 - the frame/click callback: update the armed button from the mouse
 * point, hide the panel, and when a button is armed run its action - the order
 * layer command stored in the button record (b->action(b->arg)). */
void StatusPanelClick(const void *pt)
{
    StatusPanelPressUpdate(pt);
    MapInputRestore();
    status_visible = 0;
    if (!status_pressed)
        return;
    ButtonDraw(status_button, 0);
    DirtyRectUnion(status_button_rect);
    ScreenUpdate();
    status_button->action(status_button->arg);
}

/* 0x2905c - open the panel for the displayed unit: install the mouse and frame
 * callbacks, hide the cursor and arm the focused button from the mouse point
 * (the flag is pre-seeded with the inverse so the first update always draws).
 * Does nothing while the panel is locked or no button is focused. */
void StatusPanelShow(const void *pt)
{
    const short *p = pt;
    const Rect *r = status_button_rect;
    short inside;

    if (status_lock)
        return;
    if (status_button == 0)
        return;
    status_frame_callback = (void (*)(void))StatusPanelClick;
    status_click_callback = (void (*)(void))StatusPanelClick;
    status_mouse_callback = (void (*)(void *))StatusPanelPressUpdate;
    /* the callback slot at 0x59424 is cleared */
    inside = (p[2] >= r->x1 && p[2] <= r->x2 && p[3] >= r->y1 && p[3] <= r->y2);
    SetCursor(0);
    status_visible = 1;
    status_pressed = inside ? 0 : 1;
    StatusPanelPressUpdate(pt);
}

/* 0x29354 - the command card's keyboard shortcut: the F10 record of the info
 * line first (its action opens the game menu), then the first button of the
 * displayed card whose scan code matches and which is available.  Returns 1
 * when a command was invoked. */
unsigned short StatusPanelHandleKey(const void *evt)
{
    const unsigned char *e = evt;
    unsigned short key;
    const UnitPanel *panel;
    const CommandButton *b;
    unsigned long i;

    key = e[8] | (e[9] << 8);
    if (status_lock)
        return 0;
    if (key == status_info_button.key) {
        status_info_button.action(status_info_button.arg);
        return 1;
    }
    if (status_unit_type == 0xffff)
        return 0;
    panel = &unit_panel_table[status_unit_type];
    if (panel->buttons == 0)
        return 0;
    if (status_unit->owner != 0)
        return 0;
    b = panel->buttons;
    for (i = 0; i < panel->nbuttons; i++) {
        if (key == b->key && ButtonAvailable(b)) {
            b->action(b->arg);
            return 1;
        }
        b++;
    }
    return 0;
}
