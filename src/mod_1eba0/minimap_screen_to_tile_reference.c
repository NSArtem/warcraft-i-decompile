/* codegen-compiler: 10.0a */
#include "mod_1eba0_f2.h"

void MinimapScreenToTile(short *x, short *y)
{
    short origin_x, origin_y;
    short tile_y;
    unsigned short bounded_x, bounded_y;
    long width, height;

    origin_x = side_panel_rect_x1;
    *x = (short)(*x - origin_x);
    if (*x < 0) {
        *x = 0;
    } else {
        /* The dword load at 0x1eee6 has the signed width in its high word. */
        width = *(const volatile long *)(const void *)&side_panel_rect_y2 >> 16;
        bounded_x = *(const volatile unsigned short *)(const void *)x;
        if ((long)bounded_x >= width)
            *x = (short)(minimap_input_size[0] - 1);
    }

    origin_y = side_panel_rect_y1;
    tile_y = *y;
    tile_y = (short)(tile_y - origin_y);
    *y = tile_y;
    if (tile_y < 0) {
        *y = 0;
        return;
    }
    height = *(const volatile long *)(const void *)minimap_input_size >> 16;
    bounded_y = (unsigned short)tile_y;
    if ((long)bounded_y >= height)
        *y = (short)(minimap_input_size[1] - 1);
}
