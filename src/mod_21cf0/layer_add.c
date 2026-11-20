/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_21cf0_c.h"

extern Layer layers[32];
extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
extern void ResourceReadHeaderBody(void *hdr4, void *dest);
extern void *GdsAlloc(unsigned size);
extern void __far *_fmemset(void __far *dst, int c, unsigned n);
extern void DirtyRectAddLayer(unsigned char id);

/* @0x21d0c */
void LayerAdd(Bitmap *bm, const Rect *r, unsigned short id, unsigned short res, void (*blit)())
{
    if (res != 0xffff) {
        ResourceBegin(res, 0);
        ResourceReadHeaderBody(bm, 0);
    } else {
        bm->w = r->w;
        bm->h = r->h;
        bm->data = GdsAlloc((unsigned)((*(long *)((char *)r + 6) >> 16) * (*(long *)((char *)r + 8) >> 16)));
        _fmemset(bm->data, 0, (unsigned)((*(long *)((char *)r + 6) >> 16) * (*(long *)((char *)r + 8) >> 16)));
    }
    layers[id].x = r->x;
    layers[id].y = r->y;
    layers[id].w = r->w;
    layers[id].h = r->h;
    layers[id].bm = bm;
    layers[id].blit = blit;
    layers[id].active = 1;
    DirtyRectAddLayer((unsigned char)id);
}
