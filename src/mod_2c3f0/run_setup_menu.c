/* codegen-compiler: 10.0a */
#include "war.h"

/* These two symbols are passed by address only (0x2c405, 0x2c422). */
extern const unsigned char setup_menu_top_rect[];
extern const unsigned char setup_menu_body_rect[];
extern unsigned short intro_music_started; /* 0x2c465 */
extern unsigned char palette[768]; /* 0x2c43e, 0x2c448 */
extern void *slot_file; /* 0x2c47b */
extern unsigned char cursor_layer_id; /* 0x2c492, 0x2c49c */

typedef struct Layer {
    unsigned short first_word;
    unsigned char remaining[16];
} Layer;
extern Layer layers[32]; /* 0x2c4ad */

typedef struct SetupBitmap {
    unsigned long storage[2];
} SetupBitmap;

extern void BitmapBlit(); /* 0x2c3f6, 0x2c413 */
extern void LayerAdd(SetupBitmap *, const void *, unsigned short, unsigned short, void (*)()); /* 0x2c40e, 0x2c42b */
extern unsigned long ResourceBegin(unsigned short, unsigned long *); /* 0x2c437 */
extern void *ResourceRead(void *, unsigned); /* 0x2c443 */
extern void PaletteSet(unsigned char, unsigned short, const unsigned char *); /* 0x2c454 */
extern void SetCursorShape(unsigned char); /* 0x2c45b */
extern void CursorLayerShow(void); /* 0x2c460 */
extern void PaletteFadeIn(unsigned short); /* 0x2c474 */
extern void SetupMenuLoop(void); /* 0x2c481 */
extern void PaletteFadeOut(unsigned short); /* 0x2c48b */
extern void LayerInvalidate(unsigned char); /* 0x2c497 */
extern void ResourceFreeBody(void *); /* 0x2c4c7, 0x2c4ce */

/* 0x2c3f0; called by fn_1e158. */
void RunSetupMenu(void)
{
    struct {
        SetupBitmap body;
        SetupBitmap top;
    } bitmaps;

    LayerAdd(&bitmaps.top, setup_menu_top_rect, 0x12, 0x104, BitmapBlit);
    LayerAdd(&bitmaps.body, setup_menu_body_rect, 0x13, 0xf5, BitmapBlit);
    ResourceBegin(0x106, 0);
    ResourceRead(palette, 0);
    PaletteSet(0, 0x100, palette);
    SetCursorShape(0);
    CursorLayerShow();
    if (intro_music_started == 0)
        PaletteFadeIn(20);
    slot_file = 0;
    SetupMenuLoop();
    PaletteFadeOut(20);
    LayerInvalidate(cursor_layer_id);
    layers[cursor_layer_id].first_word = 0;
    layers[0x12].first_word = 0;
    layers[0x13].first_word = 0;
    ResourceFreeBody(&bitmaps.top);
    ResourceFreeBody(&bitmaps.body);
}
