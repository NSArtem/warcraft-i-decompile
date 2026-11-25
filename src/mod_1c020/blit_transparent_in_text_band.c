/* codegen-compiler: 10.0a */
#include "mod_1c020.h"

/* 0x1c0e1, 0x1c0ed and 0x1c0fa write words at offsets 2, 10 and 6. */
struct Rect {
    short left;
    short top;
    short right;
    short bottom;
    short width;
    short height;
};

extern void BitmapBlitTransparent(short x, short y, const struct Bitmap *src, const struct Rect *srcrect);

/* 0x1c0d3 and 0x1c0e5 establish the band; 0x1c104 calls the blitter. */
void BlitTransparentInTextBand(short x, short y, const struct Bitmap *src, struct Rect *src_rect)
{
    short skip;

    skip = (short)(40 - y);
    if (skip > 0) {
        y += skip;
        src_rect->top += skip;
    }
    src_rect->height = (short)(167 - y) + 1;
    src_rect->bottom = src_rect->top + src_rect->height - 1;
    BitmapBlitTransparent(x, y, src, src_rect);
}
