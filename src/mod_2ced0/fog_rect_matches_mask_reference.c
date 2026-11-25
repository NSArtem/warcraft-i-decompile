/* codegen-compiler: 10.0a */
#include "mod_2ced0.h"

int FogRectMatchesMask(const short *xy, const short *size,
                       unsigned short mask, unsigned short expected)
{
    const unsigned short *tile;
    int rows;
    int cols;
    unsigned bits;
    unsigned wanted;

    tile = (((*(const long *)xy >> 16) * 64) + fog_map) + xy[0];
    rows = size[1];
    goto row_test;

row_start:
    cols = size[0];
col_test:
    if ((short)--cols != (short)-1)
        goto scan_tile;
    tile += 64 - size[0];
row_test:
    if ((short)--rows != (short)-1)
        goto row_start;
    return 1;

scan_tile:
    bits = (unsigned)*tile & (unsigned)mask;
    wanted = (unsigned)expected;
    ++tile;
    if (bits == wanted)
        goto col_test;
    return 0;
}
