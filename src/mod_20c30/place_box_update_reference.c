/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * PlaceBoxUpdate (0x2261c, PLACEBOX.C): per-frame placement-box overlay.
 * Converts the mouse position into a map tile, re-runs PlaceBoxCheck, redraws
 * the box border and colour when the result changes, and moves layer 21 over
 * the tile.  Called from PlaceBoxStart and the scenario start. */
#include "mod_20c30.h"

/* palette_cycles (0x628a0, 16 x 12-byte records): entry 15 (0xf) is the
 * placement-box cycle; +3 countdown, +5 current, +7 dword colour list. */
extern unsigned char palette_cycles[];
#define PC15 (palette_cycles + 15 * 12)
void Line(short x1, short y1, short x2, short y2);     /* 0x3ac10 */

/* @0x2261c */
void PlaceBoxUpdate(void)
{
    Point p;
    short mx, my;
    unsigned short r;
    short w, h;

    if (place_active[0] == 0)
        return;
    mx = ui_mouse_x - 0x48;
    my = ui_mouse_y - 0xc;
    if (mx >= 0xf0 || my >= 0xb0) {
        layers[PLACE_LAYER].active = 0;
        return;
    }
    p.x = (mx >> 4) + map_scroll_x;
    p.y = (my >> 4) + map_scroll_y;
    r = PlaceBoxCheck(p, place_type[0]);
    if (r != place_valid) {
        place_valid = r;
        w = unit_type_size[place_type[0] * 2] * 16;
        h = unit_type_size[place_type[0] * 2 + 1] * 16;
        draw_color = r != 0 ? 0xda : 0;
        cur_bitmap = &place_box_bm;
        Line(1, 1, w - 2, h - 2);
        Line(w - 2, 1, 1, h - 2);
    }
    if (PC15[3] == 1 && PC15[5] == 0)
        *(void **)(PC15 + 7) = place_valid == 0 ? place_colors_bad : place_colors_ok;
    mx &= 0xf0;
    my &= 0xf0;
    layers[PLACE_LAYER].x = mx + 0x48;
    layers[PLACE_LAYER].y = my + 0xc;
    layers[PLACE_LAYER].active = 1;
}
