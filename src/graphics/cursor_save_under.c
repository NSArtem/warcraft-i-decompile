/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_320f0 (0x320f0..0x32188), DBG style. */
#include "graphics.h"

/* @0x320f0 */
void CursorSaveUnder(void)
{
    cursor_save_rect.x1 = layers[0].x;
    cursor_save_rect.y1 = layers[0].y;
    cursor_save_bm.w = cursor_save_rect.w = layers[0].w;
    cursor_save_bm.h = cursor_save_rect.h = layers[0].h;
    cursor_save_rect.x2 = cursor_save_rect.x1 + cursor_save_rect.w - 1;
    cursor_save_rect.y2 = cursor_save_rect.y1 + cursor_save_rect.h - 1;
    cur_bitmap = &cursor_save_bm;
    BitmapBlit(0, 0, &backbuf_bm, &cursor_save_rect);
    cur_bitmap = &backbuf_bm;
}
