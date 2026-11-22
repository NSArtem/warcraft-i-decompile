/* codegen-compiler: 10.0a */
#include "mod_1eba0_f2.h"

extern void BitmapBlit(void); /* Address pushed at 0x1eba5. */
extern void LayerAdd(Bitmap *, const Rect *, int, unsigned int, void (*)(void)); /* Call at 0x1ebcc. */

void MinimapPanelInit(void)
{
    short size, left, top, right, bottom;

    LayerAdd(&minimap_panel_bitmap, &score_panel_rect, 0x11,
             (unsigned short)(scenario_race + 0xe2), BitmapBlit);
    map_aux_handler = MinimapBeginScrollInput;
    size = 0x40;
    minimap_draw_size[0] = size;
    minimap_draw_size[1] = size;
    left = 3;
    minimap_draw_rect[0] = left;
    top = 6;
    minimap_draw_rect[1] = top;
    minimap_pixel_offset = 0x1b3;
    side_panel_rect_x1 = left;
    side_panel_rect_y1 = top;
    minimap_input_size[0] = size;
    minimap_input_size[1] = size;
    right = 0x42;
    minimap_draw_rect[2] = right;
    bottom = 0x45;
    minimap_draw_rect[3] = bottom;
    side_panel_rect_x2 = right;
    side_panel_rect_y2 = bottom;
    minimap_redraw_countdown = 0x28;
}
