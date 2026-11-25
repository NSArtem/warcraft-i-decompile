/* codegen-compiler: 10.0a */
#include "mod_2ced0.h"

extern unsigned short fn_13348(short x, short y, unsigned mask); /* 0x2e536–0x2e540. */

typedef union {
    unsigned long packed;
    short half[2];
} PerimeterPair;

typedef struct {
    PerimeterPair target;
    PerimeterPair size;
    unsigned long start;
    unsigned long dir;
} PerimeterState;

int FindNearbyClearTile(short *x, short *y,
                        unsigned long packed_size, unsigned long packed_target)
{
    PerimeterState state;
    unsigned long tx;
    unsigned long ty;
    unsigned long count;
    short initial_x;
    short initial_y;
    short cx;
    short cy;
    unsigned short x_side;
    unsigned index;
    int ix;
    int iy;

    state.size.packed = packed_size;
    state.target.packed = packed_target;
    tx = *(volatile unsigned long *)&state.target.packed;
    initial_x = *x;
    if ((short)tx <= initial_x) {
        cx = (short)(initial_x - 1);
        x_side = 0;
    } else {
        cx = (short)((unsigned long)initial_x + state.size.packed);
        x_side = 1;
    }
    ty = *(volatile unsigned long *)((char *)&state.target + 2);
    initial_y = *y;
    if ((short)ty <= initial_y) {
        cy = (short)(initial_y - 1);
        state.start = 0;
    } else {
        cy = (short)((unsigned long)initial_y + *(volatile unsigned long *)((char *)&state.size + 2));
        state.start = 1;
    }
    state.start = perimeter_start_direction[(unsigned short)state.start][x_side];

    while ((*(volatile long *)((char *)&state.target + 2) >> 16) < 12) {
        state.dir = state.start;
        state.size.half[0] += 2;
        state.size.half[1] += 2;
        do {
            if ((unsigned short)(state.dir & 1) != 0)
                count = *(volatile unsigned long *)((char *)&state.size + 2);
            else
                count = state.size.packed;
            while ((short)--count != (short)-1) {
                if (cx < 0 || cy < 0)
                    goto step;
                ix = cx;
                if (ix >= 64)
                    goto step;
                iy = cy;
                if (iy >= 64)
                    goto step;
                if (fn_13348((short)ix, (short)iy, 0x3cc) == 0) {
                    *x = cx;
                    *y = cy;
                    return 1;
                }
step:
                index = (unsigned short)state.dir;
                cx += step4_dx[index];
                cy += step4_dy[index];
            }
            index = (unsigned short)state.dir;
            cx -= step4_dx[index];
            cy -= step4_dy[index];
            state.dir = index + 1;
            state.dir = (unsigned short)(state.dir & 3);
        } while ((unsigned short)state.dir != (unsigned short)state.start);
        index = (unsigned short)state.dir;
        cx -= perimeter_expand_dx[index];
        cy -= perimeter_expand_dy[index];
    }
    return 0;
}
