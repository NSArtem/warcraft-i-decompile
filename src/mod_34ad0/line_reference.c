/* codegen-compiler: 10.0a */
#include "mod_34ad0_c.h"

typedef struct Bitmap {
    short width;
    short height;
    unsigned char *data;
} Bitmap;

extern Bitmap *cur_bitmap;
extern unsigned char draw_color;
extern void VLine(short x, unsigned short y, unsigned short len);
extern void HLine(short x, unsigned short y, unsigned short len);

void Line(short x0, short y0, short x1, short y1)
{
    short dx, dy, t, err, sx, sy;
    unsigned char *base;

    if (x0 > x1) {
        dx = x0 - x1;
    } else {
        dx = x1 - x0;
    }
    if (y0 > y1) {
        dy = y0 - y1;
    } else {
        dy = y1 - y0;
    }
    if (dx == 0) {
        if (y0 < y1) {
            VLine(x0, y0, dy);
        } else {
            VLine(x0, y1, dy);
        }
        return;
    }
    if (dy == 0) {
        if (x0 < x1) {
            HLine(x0, y0, dx);
        } else {
            HLine(x1, y0, dx);
        }
        return;
    }
    base = cur_bitmap->data;
    if ((dy < dx && x0 > x1) || (dy > dx && y0 > y1)) {
        t = x0; x0 = x1; x1 = t;
        t = y0; y0 = y1; y1 = t;
    }
    if (x0 > x1) {
        sx = -1;
    } else {
        sx = 1;
    }
    if (y0 > y1) {
        sy = -1;
    } else {
        sy = 1;
    }
    err = 0;
    if (dx > dy) {
        while (x0 <= x1) {
            if (err >= dx) {
                err -= dx;
                y0 += sy;
            }
            base[x0 + y0 * cur_bitmap->width] = draw_color;
            err += dy;
            x0++;
        }
    } else {
        while (y0 <= y1) {
            if (err > dy) {
                err -= dy;
                x0 += sx;
            }
            base[x0 + y0 * cur_bitmap->width] = draw_color;
            err += dx;
            y0++;
        }
    }
}
