/* codegen-compiler: 10.0a */
#include "mod_2ced0_c.h"

extern unsigned char *dat_522a8[];
extern unsigned char dat_552a8[16];
extern void (*sprite_blitters[8])(short, short, const Bitmap *, const Rect *);
extern void GrpFrameInfo(const unsigned char *grp, unsigned frame, Bitmap *out, short *xoff, short *yoff, short *maxw, short *maxh);

/* @0x2d704 */
void UnitDrawSprite(const Unit *u, short scroll_x, short scroll_y)
{
    Rect r;
    short cw, ch;
    Bitmap bm;
    short xoff, yoff, maxw, maxh;
    short x, y, dx, dy;

    if ((u->sflags & 3) != 0) {
        return;
    }
    GrpFrameInfo(dat_522a8[u->type], (unsigned char)(u->frame_base + dat_552a8[u->dir * 2]), &bm, &xoff, &yoff, &maxw, &maxh);
    x = (short)(u->x - scroll_x - maxw / 2 + xoff);
    if (x >= 240) {
        return;
    }
    y = (short)(u->y - scroll_y - maxh / 2 + yoff);
    if (y >= 176) {
        return;
    }
    if (x + bm.w <= 0 || y + bm.h <= 0) {
        return;
    }
    dx = (short)-x;
    if (dx < 0) {
        r.x1 = 0;
        cw = bm.w;
    } else {
        r.x1 = dx;
        x = (short)(x + dx);
        cw = (short)(bm.w - dx);
    }
    dy = (short)-y;
    if (dy < 0) {
        r.y1 = 0;
        ch = bm.h;
    } else {
        r.y1 = dy;
        y = (short)(y + dy);
        ch = (short)(bm.h - dy);
    }
    if (cw >= 240 - x) {
        cw = (short)(240 - x);
    }
    if (ch >= 176 - y) {
        ch = (short)(176 - y);
    }
    r.x2 = (short)(r.x1 + cw - 1);
    r.y2 = (short)(r.y1 + ch - 1);
    sprite_blitters[u->dir]((short)(x + 0x48), (short)(y + 0xc), &bm, &r);
}
