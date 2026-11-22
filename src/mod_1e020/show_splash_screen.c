/* codegen-compiler: 10.0a */
struct Rect {
    short left, top, right, bottom;
};

#include "mod_1e020.h"

typedef struct Bitmap {
    unsigned long header_words[2];
} Bitmap;

extern void SndLoadTable(const unsigned short *ids);
extern void SndPlay(unsigned id);
extern void BitmapBlit(void);
extern void LayerAdd(Bitmap *bm, const Rect *r, unsigned short id,
                     unsigned short res, void (*blit)(void));
extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
extern void *ResourceRead(void *dest, unsigned count);
extern void PaletteSet(unsigned char first, unsigned short count,
                       const unsigned char *rgb);
extern void LayerInvalidate(unsigned char id);
extern void PaletteFadeIn(unsigned short steps);
extern short WaitInputOrTimeout(short ticks);
extern void PaletteFadeOut(unsigned short steps);
extern void ResourceFreeBody(void *hdr);
extern void SndReleaseAll(void);

void ShowSplashScreen(void)
{
    Bitmap bitmap_header;

    SndLoadTable(splash_sound_table);
    SndPlay(0);
    LayerAdd(&bitmap_header, &full_screen_rect, 13, 0xda, BitmapBlit);
    ResourceBegin(0xdb, 0);
    ResourceRead(palette, 0);
    PaletteSet(0, 256, palette);
    LayerInvalidate(cursor_layer_id);
    layers[cursor_layer_id].first_word = 0;
    PaletteFadeIn(250);
    PaletteFadeOut((unsigned short)(WaitInputOrTimeout(45) != 0 ? 1 : 250));
    status_aux_flag = 0;
    ResourceFreeBody(&bitmap_header);
    SndReleaseAll();
    SndLoadTable(0);
}
