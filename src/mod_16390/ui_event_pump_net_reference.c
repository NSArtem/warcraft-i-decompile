/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x185b4 (assumes int NetSendLocalEvent(Event *ev)) */
void UiEventPumpNet(void)
{
    Event ev;
    short ok;
    unsigned char id;

    ui_net_forward = 1;
    if (net_play_flag != 0) {
        if (screen_mode != 0) {
            id = cursor_layer_id;
            if (mouse_raw_x != I16(&layers[id].x) + I16(&cursor_hotspot_x) ||
                mouse_raw_y != I16(&layers[id].y) + I16(&cursor_hotspot_y)) {
                CursorMoveTo(mouse_raw_x, mouse_raw_y);
            }
            ok = (short)((int (*)(Event *))NetSendLocalEvent)(&ev);
        } else {
            ok = (short)NetQueryRemoteEvent(&ev);
            if (ok) {
                id = cursor_layer_id;
                if (I16(&ev.x) != I16(&layers[id].x) + I16(&cursor_hotspot_x) ||
                    I16(&ev.y) != I16(&layers[id].y) + I16(&cursor_hotspot_y)) {
                    CursorMoveTo(I16(&ev.x), I16(&ev.y));
                }
            }
        }
    } else {
        id = cursor_layer_id;
        if (mouse_raw_x != I16(&layers[id].x) + I16(&cursor_hotspot_x) ||
            mouse_raw_y != I16(&layers[id].y) + I16(&cursor_hotspot_y)) {
            CursorMoveTo(mouse_raw_x, mouse_raw_y);
        }
        ok = (short)EvtGet(&ev);
    }
    if (ok) {
        ui_mouse_x = ev.x;
        ui_mouse_y = ev.y;
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
