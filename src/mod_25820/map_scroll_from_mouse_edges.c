/* codegen-compiler: 10.0a */
#include "mod_25820.h"

/* 0x25acf and 0x25b0e test the far edges; 0x25b40 clears the target. */
unsigned short MapScrollFromMouseEdges(short enable_edges)
{
    short dx;
    short dy;
    short pos;
    unsigned short shape;

    if (enable_edges != 0) {
        pos = ui_mouse_x;
        if (pos <= 8 && map_scroll_x > 0)
            dx = -1;
        else if (pos >= 311 && map_scroll_x < map_scroll_x_max)
            dx = 1;
        else
            dx = 0;

        pos = ui_mouse_y;
        if (pos <= 8 && map_scroll_y > 0)
            dy = -1;
        else if (pos >= 191 && map_scroll_y < map_scroll_y_max)
            dy = 1;
        else
            dy = 0;
    } else {
        dy = enable_edges;
        dx = 0;
    }

    shape = MapScrollApplyDeltas(dx, dy);
    map_order_target = 0;
    return shape;
}
