/* codegen-compiler: 10.0a */
/* 0x187d4: blit one clipped line of the credits text page. */
#include "mod_16390.h"

void OutroDrawLine(short x, short y, Bitmap *src, Rect *r)
{
    short dy = 0x28 - y;

    if (dy > 0) {
        y += dy;
        r->y += dy;
    }
    r->h = 0xa7 - y + 1;
    r->bottom = r->y + r->h - 1;
    BitmapBlitTransparent(x, y, src, r);
}
