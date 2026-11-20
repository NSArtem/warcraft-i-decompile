/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned short terrain_rect_mask_table[];
extern void (*terrain_rect_cb)(int, int, unsigned); /* 0x5a458 */

/* @0x2c208 */
void TerrainFillRectMask(unsigned char *rect, unsigned kind)
{
    unsigned mask;
    int x, y, x1, y1, dx, dy;

    terrain_rect_cb = (void (*)(int, int, unsigned))TerrainApplyCellFlags;
    mask = terrain_rect_mask_table[kind & 0xff];
    x = rect[0] >> 1;
    y = rect[1] >> 1;
    x1 = rect[2] >> 1;
    y1 = rect[3] >> 1;
    if (y < y1) {
        dx = 0;
        dy = 1;
    } else {
        dx = 1;
        dy = 0;
    }
    do {
        terrain_rect_cb(x, y, mask);
        x += dx;
        y += dy;
    } while (x <= x1 && y <= y1);
}
