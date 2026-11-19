/* codegen-compiler: 10.0a */
/* mod_295d0.  ClipBox 0x2a1f4: turn a centre point into a clipped box.  The
 * callers pass a size (0x15 or 0x0b); the rectangle is centred on the point
 * and clipped to the 64x64 map, x/y coming back as the top-left corner and
 * w/h as the size still inside the map.  All four are 32-bit cells (the
 * callers keep them in dwords); the size is the 5th (stack) argument.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x2a1f4 */
void ClipBox(int *x, int *y, int *w, int *h, int size)
{
    int half;
    int x1, y1;
    int x2, y2;
    int ww, hh;

    half = size / 2;
    x1 = *x - half;
    y1 = *y - half;
    ww = size;
    hh = size;
    x2 = size + x1;
    if (x1 < 0) {
        ww = x2;
        x1 = 0;
    } else {
        if (x2 >= 0x40)
            ww = 0x40 - x1;
    }
    y2 = size + y1;
    if (y1 < 0) {
        hh = y2;
        y1 = 0;
    } else {
        if (y2 >= 0x40)
            hh = 0x40 - y1;
    }
    *x = x1;
    *y = y1;
    *w = ww;
    *h = hh;
}
