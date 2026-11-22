/* codegen-compiler: 10.0a */
#include "mod_1c9c0.h"

void UnitUpdateGraphicsIndex(Unit *u)
{
    unsigned char *p = (unsigned char *)u;
    unsigned char index;
    unsigned char mask;
    unsigned short flags;

    index = p[0x1b];
    if ((int)index < 2 || (int)index > 3) {
        flags = *(volatile unsigned short *)(p + 0x10);
        if ((int)(unsigned short)(flags & 0x80) != 0)
            index = p[0x1b];
        else
            index = unit_type_graphics_map[p[0x1b]][0];
    } else {
        mask = (unsigned char)(((volatile unsigned char *)p)[0x49] & 0x20);
        if ((int)mask != 0) {
            mask = (unsigned char)(((volatile unsigned char *)p)[0x49] & 0x80);
            if ((int)mask != 0) {
                if ((int)index == 2)
                    p[0x1d] = 0x36;
                else
                    p[0x1d] = 0x37;
            } else {
                if ((int)index == 2)
                    p[0x1d] = 0x34;
                else
                    p[0x1d] = 0x35;
            }
            goto double_index;
        }
    }
    p[0x1d] = index;

double_index:
    index = p[0x1d];
    index += index;
    p[0x1d] = index;
    if (p[0x1e] == 0) {
        index = p[0x1b];
        if ((int)index == 0x33 || (int)index == 0x15 || (int)index == 0x18)
            return;
    } else {
        index = ((volatile unsigned char *)p)[0x1e];
        if ((int)index != 4)
            return;
        index = p[0x1b];
        if ((int)index == 0x0f) {
            p[0x1d] = 0x21;
            return;
        }
        if ((int)index == 0x32 || (int)index == 0x33)
            return;
    }
    ++p[0x1d];
}
