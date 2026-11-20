/* codegen-compiler: 10.0a */
#include "mod_1af20_c1.h"

extern unsigned short *fog_map;
extern unsigned short map_scroll_x;
extern unsigned short map_scroll_y;
extern unsigned char *dat_5a874;
extern void FogDrawCell(unsigned short cell, unsigned char *dst);

/* @0x1af90 */
void FogDrawViewport(void)
{
    unsigned short *src;
    unsigned char *dst;
    unsigned short row;
    unsigned short col;

    src = fog_map;
    src += map_scroll_y * 64 + map_scroll_x;
    dst = dat_5a874;
    row = 11;
    dst += 0xf48;
    while (--row != 0xffff) {
        col = 15;
        while (--col != 0xffff) {
            FogDrawCell(*src, dst);
            src++;
            dst += 0x10;
        }
        src += 0x31;
        dst += 0x1310;
    }
}
