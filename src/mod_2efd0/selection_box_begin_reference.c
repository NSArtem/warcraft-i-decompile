/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* SelectionBoxBegin (0x2f350): a press inside the map viewport starts a drag
 * selection - confine the mouse to the view, install the box callbacks and
 * remember the anchor pixel.  Nothing happens while a modal screen or the
 * build-placement box owns the input. */
#include "mod_2efd0.h"

/* @0x2f350 */
void SelectionBoxBegin(Event *ev)
{
    if (fn_2b308() != 0 || PlaceBoxActive() != 0)
        return;
    MouseSetRange(map_view_rect[0], map_view_rect[1],
                  map_view_rect[2], map_view_rect[3]);
    status_frame_callback = (void (*)(void))SelectionBoxFrame;
    status_click_callback = (void (*)(void))SelectionBoxFrame;
    status_mouse_callback = (void (*)(void *))SelectionBoxTrack;
    dialog_pre_event = 0;
    SetCursorShape(6);
    selection_box.anchor_x = ev->x;
    selection_box.anchor_y = ev->y;
}
