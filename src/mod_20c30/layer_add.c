/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * LayerAdd (0x21d0c, mod_21cf0): register a bitmap as screen layer `id`.
 * With res != 0xffff the bitmap is a DATA.WAR resource (its {w,h} header and
 * body are read into the caller's descriptor); otherwise the size comes from
 * the Rect and the pixels are a cleared GdsAlloc buffer.  The 18-byte layer
 * record is `layers` (graphics.h).
 *
 * Source idiom: the original reads the packed Rect pair {w,h} twice as
 * overlapping 32-bit loads (`mov eax,[r+6]; sar eax,16` for w,
 * `mov edx,[r+8]; sar edx,16` for h).  Writing the pair through a long view
 * reproduces that; a plain `r->w * r->h` gives movsx and does not match. */
#include "mod_20c30.h"

#define RECT_WORD(r, off) (*(long *)((char *)(r) + (off) - 2) >> 16)

/* @0x21d0c */
void LayerAdd(Bitmap *bm, const Rect *r, unsigned short id, unsigned short res,
              void (*blit)())
{
    if (res != 0xffff) {
        ResourceBegin(res, 0);
        ResourceReadHeaderBody(bm, 0);
    } else {
        bm->w = r->w;
        bm->h = r->h;
        bm->data = GdsAlloc(RECT_WORD(r, 8) * RECT_WORD(r, 0xa));
        _fmemset(bm->data, 0, RECT_WORD(r, 8) * RECT_WORD(r, 0xa));
    }
    layers[id].x = r->x1;
    layers[id].y = r->y1;
    layers[id].w = r->w;
    layers[id].h = r->h;
    layers[id].data = bm;
    layers[id].callback = blit;
    layers[id].active = 1;
    DirtyRectAddLayer(id);
}
