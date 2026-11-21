/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_3cb10_c.h"

/* @0x3cb10 */
int __cdecl RectClip(Rect *src, Rect *dst)
{
    if (src->x >= src->w || src->y >= src->h || src->x2 < 0 || src->y2 < 0) {
        return 1;
    }
    if (src->x < 0) {
        dst->x -= src->x;
        src->x = 0;
    }
    if (src->x2 >= src->w) {
        src->x2 = src->w - 1;
    }
    if (src->y < 0) {
        dst->y -= src->y;
        src->y = 0;
    }
    if (src->y2 >= src->h) {
        src->y2 = src->h - 1;
    }
    if (dst->x < 0) {
        src->x -= dst->x;
        dst->x = 0;
    } else if (dst->x >= dst->w) {
        return 1;
    }
    if (dst->y < 0) {
        src->y -= dst->y;
        dst->y = 0;
    } else if (dst->y >= dst->h) {
        return 1;
    }
    dst->x2 = dst->x + src->x2 - src->x;
    dst->y2 = dst->y + src->y2 - src->y;
    if (dst->x2 < 0 || dst->y2 < 0) {
        return 1;
    }
    dst->x2 -= dst->w - 1;
    if (dst->x2 > 0) {
        src->x2 -= dst->x2;
    }
    dst->y2 -= dst->h - 1;
    if (dst->y2 > 0) {
        src->y2 -= dst->y2;
    }
    src->h = src->y2 - src->y + 1;
    src->w = src->x2 - src->x + 1;
    return 0;
}
