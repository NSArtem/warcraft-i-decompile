/* codegen-compiler: 10.0a */
#include "mod_1af20_c1.h"

extern unsigned short *fog_cell_table;
extern void FillBlack16(unsigned char *dst);
extern void MiniTileMasked(unsigned short tile, unsigned char *dst);

/* @0x1af20 */
void FogDrawCell(unsigned short c, unsigned char *dst)
{
    unsigned short *p;

    c = (unsigned char)c;
    c &= 0x1f;
    if (c == 0)
        return;
    if (c == 10) {
        FillBlack16(dst);
        return;
    }
    p = (unsigned short *)((char *)fog_cell_table + c * 8);
    MiniTileMasked(*p++, dst);
    MiniTileMasked(*p++, dst + 8);
    MiniTileMasked(*p++, dst + 0xa00);
    MiniTileMasked(*p, dst + 0xa08);
}
