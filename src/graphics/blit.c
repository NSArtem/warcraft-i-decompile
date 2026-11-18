/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Bitmap blitters and the solid-fill primitive (modules mod_32410,
 * mod_325d0, mod_326a0, mod_326f0, mod_31fc0).  Reference C: near misses
 * (word sign-extension idiom and argument order), difftested in
 * tests/test_graphics_lib.py.
 */
#include <string.h>
#include "graphics.h"

/* @0x31fc0 */
void BitmapClear(unsigned char color)
{
    memset(cur_bitmap->data, color, cur_bitmap->w * cur_bitmap->h);
}

/* @0x326a0 */
void FillRect(short x, short y, unsigned short w, unsigned short h)
{
    short i;

    for (i = 0; i < (short)h; i++)
        HLine(x, y + i, w);
}

/* @0x32410 */
void BitmapBlit(short x, short y, const Bitmap *src, const Rect *srcrect)
{
    Rect r = *srcrect;
    Rect bounds;

    bounds.x1 = x;
    bounds.y1 = y;
    bounds.w = cur_bitmap->w;
    bounds.h = cur_bitmap->h;
    if (RectClip(&r, &bounds) != 0)
        return;
    RectCopy(src->data + src->w * r.y1 + r.x1,
             cur_bitmap->data + cur_bitmap->w * bounds.y1 + bounds.x1,
             src->w - r.w, cur_bitmap->w - r.w, r.w, r.h);
}

/* @0x325d0 */
void BitmapBlitTransparent(short x, short y, const Bitmap *src, const Rect *srcrect)
{
    Rect r = *srcrect;
    Rect bounds;

    bounds.x1 = x;
    bounds.y1 = y;
    bounds.w = cur_bitmap->w;
    bounds.h = cur_bitmap->h;
    if (RectClip(&r, &bounds) != 0)
        return;
    RectCopyTransparent(src->data + src->w * r.y1 + r.x1,
                        cur_bitmap->data + cur_bitmap->w * bounds.y1 + bounds.x1,
                        src->w - r.w, cur_bitmap->w - r.w, r.w, r.h);
}

/* @0x326f0 */
void BitmapBlitTransparentAll(short x, short y, const Bitmap *src)
{
    Rect r;

    r.x1 = 0;
    r.y1 = 0;
    r.x2 = src->w - 1;
    r.y2 = src->h - 1;
    r.w = src->w;
    r.h = src->h;
    BitmapBlitTransparent(x, y, src, &r);
}
