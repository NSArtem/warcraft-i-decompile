/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 */
/* The records as this function uses them (docs/subsystems/mod_3aac0_c.md). */
typedef struct Rect { short x, y, a, b, w, h; } Rect;
typedef struct Bitmap { short w, h; unsigned char *data; } Bitmap;

extern Bitmap *cur_bitmap;
short __cdecl RectClip(Rect *src, Rect *dst);
void __cdecl RectCopyTransparentFlipH(const unsigned char *src, unsigned char *dst, short src_skip, short dst_skip, short width, short height);

/* @0x3aac0 */
void BitmapBlitTransparentFlipH(short x, short y, const Bitmap *src, const Rect *srcrect)
{
    Rect d;
    Rect s;

    s = *srcrect;
    s.w = src->w;
    s.h = src->h;
    d.a = 0;
    d.b = 0;
    d.x = x;
    d.y = y;
    d.w = cur_bitmap->w;
    d.h = cur_bitmap->h;
    if (RectClip(&s, &d) == 0) {
        RectCopyTransparentFlipH(
            src->data + srcrect->x * (unsigned short)s.y + (srcrect->x - s.x - s.w),
            cur_bitmap->data + cur_bitmap->w * (unsigned short)d.y + d.x,
            (short)(srcrect->x + s.w),
            (short)(cur_bitmap->w - s.w),
            s.w,
            s.h);
    }
}
