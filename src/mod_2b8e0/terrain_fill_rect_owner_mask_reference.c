/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned short owner_block_mask[];       /* 0x51dca */
extern void (*terrain_rect_cb)(int, int, unsigned); /* 0x5a458 */
extern void TerrainRoadCell(int x, int y, unsigned short mask); /* 0x2c100 */

/* @0x2c1e8 */
void TerrainFillRectOwnerMask(unsigned char *rect, unsigned owner)
{
    unsigned mask;
    int x, y, x1, y1, dx, dy;

    terrain_rect_cb = (void (*)(int, int, unsigned))TerrainRoadCell;
    mask = owner_block_mask[owner & 0xff];
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
