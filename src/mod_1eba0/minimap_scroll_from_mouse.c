/* codegen-compiler: 10.0a */
#include "mod_1eba0_f2.h"

extern void MapViewSetScroll(int, int); /* Call at 0x1ef99. */

void MinimapScrollFromMouse(void)
{
    struct {
        short y;
        short pad_y;
        short x;
        short pad_x;
    } pos;
    int sx, sy;

    pos.x = (short)(ui_mouse_x - 7);
    pos.y = (short)(ui_mouse_y - 5);
    MinimapScreenToTile(&pos.x, &pos.y);
    if ((unsigned short)*(const volatile long *)(const void *)&pos.x != map_scroll_x ||
        (unsigned short)*(const volatile long *)(const void *)&pos.y != map_scroll_y) {
        /* The target reads across the slot boundary, then discards the low word. */
        sy = *(const volatile long *)(const void *)((const char *)&pos.y - 2) >> 16;
        sx = *(const volatile long *)(const void *)&pos.pad_y >> 16;
        MapViewSetScroll(sx, sy);
    }
}
