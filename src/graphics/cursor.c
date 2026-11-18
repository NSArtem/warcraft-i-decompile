/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Cursor, layer and dirty-rectangle composition (modules mod_317b0,
 * mod_320f0, mod_33040, mod_32f10).  Reference C (CursorSaveUnder is the
 * one function of this group that matches: src/graphics/cursor_save_under.c),
 * difftested in tests/test_graphics_lib.py.
 */
#include "graphics.h"

void DirtyRectAlignAndPresent(void);                      /* 0x33aa0 */

/* @0x317b0 */
void CursorSetImage(const void *desc)
{
    const CursorImage *ci = (const CursorImage *)desc;

    LayerInvalidate(cursor_layer_id);
    cursor_hotspot_x = ci->hot_x;
    cursor_hotspot_y = ci->hot_y;
    cursor_bitmap = ci->bm;
    layers[cursor_layer_id].data = (void *)&ci->bm;
    layers[cursor_layer_id].w = ci->bm.w;
    layers[cursor_layer_id].h = ci->bm.h;
    if (mouse_raw_x != layers[cursor_layer_id].x + cursor_hotspot_x
        || mouse_raw_y != layers[cursor_layer_id].y + cursor_hotspot_y)
        CursorMoveTo(mouse_raw_x, mouse_raw_y);
    LayerInvalidate(cursor_layer_id);
}

/* @0x330a0 */
void CursorMoveTo(short x, short y)
{
    LayerInvalidate(cursor_layer_id);
    layers[cursor_layer_id].x = x - cursor_hotspot_x;
    layers[cursor_layer_id].y = y - cursor_hotspot_y;
    LayerInvalidate(cursor_layer_id);
    mouse_x = x;
    mouse_y = y;
}

/* @0x32188 */
void CursorRestoreUnder(void)
{
    cursor_save_rect.x1 = 0;
    cursor_save_rect.y1 = 0;
    cursor_save_rect.x2 = cursor_save_bm.w - 1;
    cursor_save_rect.y2 = cursor_save_bm.h - 1;
    cur_bitmap = &backbuf_bm;
    BitmapBlit(layers[0].x, layers[0].y, &cursor_save_bm, &cursor_save_rect);
}

/* @0x32f10 */
void LayerFillCallback(short x, short y, Rect *r, void *data)
{
    draw_color = 0;
    FillRect(dirty_x1, dirty_y1, dirty_w, dirty_h);
}

/* @0x321e8 */
void ScreenUpdate(void)
{
    Bitmap *saved;
    Rect r;
    int i;

    if (dirty_x1 >= 320 || dirty_y1 >= 200)
        return;
    if (dirty_x1 < 0) dirty_x1 = 0;
    if (dirty_y1 < 0) dirty_y1 = 0;
    if (dirty_x2 >= 320) dirty_x2 = 319;
    if (dirty_y2 >= 200) dirty_y2 = 199;
    dirty_w = dirty_x2 - dirty_x1 + 1;
    dirty_h = dirty_y2 - dirty_y1 + 1;
    if (dirty_w < 1 || dirty_h < 1)
        return;
    saved = cur_bitmap;
    cur_bitmap = &backbuf_bm;
    r.w = dirty_w;
    r.h = dirty_h;
    for (i = 31; i >= 0; i--) {
        if (!layers[i].active)
            continue;
        r.x1 = dirty_x1 - layers[i].x;
        r.y1 = dirty_y1 - layers[i].y;
        r.x2 = r.x1 + r.w - 1;
        r.y2 = r.y1 + r.h - 1;
        if (i == 0)
            CursorSaveUnder();
        layers[i].callback(dirty_x1, dirty_y1, &r, layers[i].data);
    }
    DirtyRectAlignAndPresent();
    if (layers[0].active)
        CursorRestoreUnder();
    dirty_x1 = 0x7fff;
    dirty_y1 = 0x7fff;
    dirty_x2 = -0x8000;
    dirty_y2 = -0x8000;
    dirty_w = 0;
    dirty_h = 0;
    cur_bitmap = saved;
}
