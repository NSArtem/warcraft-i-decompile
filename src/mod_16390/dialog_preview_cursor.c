/* codegen-compiler: 10.0a */
/* 0x16f5c: hide the cursor layer while the mouse is over the map preview. */
#include "mod_16390.h"

void DialogPreviewCursor(void)
{
    if (mouse_in_preview != 0) {
        if (ui_mouse_x >= preview_rect[0] && ui_mouse_x <= preview_rect[2]
            && ui_mouse_y >= preview_rect[1] && ui_mouse_y <= preview_rect[3])
            return;
        mouse_in_preview = 0;
        CursorLayerShow();
    } else {
        if (ui_mouse_x < preview_rect[0] || ui_mouse_x > preview_rect[2])
            return;
        if (ui_mouse_y < preview_rect[1] || ui_mouse_y > preview_rect[3])
            return;
        mouse_in_preview = 1;
        LayerInvalidate(cursor_layer_id);
        layers[cursor_layer_id].active = 0;
    }
}
