/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -of -zp2 */
#include "mod_33b00_c.h"

typedef struct BlitRect {
    short left;
    short top;
    short right;
    short bottom;
    short w;
    short h;
} BlitRect;

extern void BitmapBlit(short x, short y, const Bitmap *src, const Rect *srcrect);

/* @0x33b00 */
void BitmapBlitAll(short x, short y, const Bitmap *src)
{
    BlitRect r;

    r.left = 0;
    r.top = 0;
    r.w = src->width;
    r.right = r.w - 1;
    r.h = src->height;
    r.bottom = r.h - 1;
    BitmapBlit(x, y, src, (const Rect *)&r);
}
