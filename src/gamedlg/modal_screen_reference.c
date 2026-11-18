/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The modal screen around a dialog page: on open, tint the image dark red and
 * give the page a full-screen layer of its own (a copy of the current image,
 * with the in-game UI layers 13..22 hidden); on close, undo everything.  Nested
 * dialogs only move the depth counter. */
#include "gamedlg.h"

/* @0x1a560 */
void ModalScreen(short on, short dim)
{
    unsigned short w = 0x140;
    unsigned short h = 0xc8;
    unsigned short i;

    if (dialog_enabled == 0)
        return;
    dialog_active = 1;
    if (on) {
        if (++dialog_depth != 1)
            return;
        NetPumpEvents();
        if (dim)
            DimScreenImage();
        dialog_bitmap.w = w;
        dialog_bitmap.h = h;
        dialog_buffer = GdsAlloc(0xfa00);
        cur_bitmap = &dialog_bitmap;
        BitmapBlitAll(0, 0, &backbuf_bm);
        layers[23].x = 0;
        layers[23].y = 0;
        layers[23].w = w;
        layers[23].h = h;
        layers[23].data = &dialog_bitmap;
        layers[23].draw = BitmapBlit;
        layers[23].active = 1;
        for (i = 0; i < 10; i++) {
            dialog_layer_state[i] = layers[13 + i].active;
            layers[13 + i].active = 0;
        }
    } else {
        if (--dialog_depth != 0)
            return;
        game_speed_cache = -1;
        GdsFree(dialog_buffer);
        dialog_buffer = 0;
        layers[23].active = 0;
        PaletteSet(0, 0x100, palette_target);
        for (i = 0; i < 10; i++)
            layers[13 + i].active = dialog_layer_state[i];
        DirtyRectAddBox(0, 0, 0x13f, 0xc7);
        ScreenUpdate();
        PaletteSet(0, 0x100, palette);
        GameScreenInputInit();
    }
}
