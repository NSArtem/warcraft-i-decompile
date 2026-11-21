/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x184cc */
void UiEventPump(void)
{
    Event ev;
    short ok;
    unsigned char id;

    ui_net_forward = 0;
    id = cursor_layer_id;
    if (mouse_raw_x != I16(&layers[id].x) + I16(&cursor_hotspot_x) ||
        mouse_raw_y != I16(&layers[id].y) + I16(&cursor_hotspot_y)) {
        CursorMoveTo(mouse_raw_x, mouse_raw_y);
    }
    ok = (short)EvtGet(&ev);
    if (ok) {
        ui_mouse_x = ev.x;
        ui_mouse_y = ev.y;
    } else {
        ui_mouse_x = mouse_raw_x;
        ui_mouse_y = mouse_raw_y;
    }
    if (dialog_pre_event != 0) {
        dialog_pre_event();
    }
    if (ok) {
        EvtProcess(&ev);
        if (event_handler_table[ev.sub] != 0) {
            event_handler_table[ev.sub](&ev);
        }
    }
}
