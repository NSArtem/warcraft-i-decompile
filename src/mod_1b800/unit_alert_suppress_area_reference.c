/* codegen-compiler: 10.0a */
/* mod_1b800 (reference C, not T3).  UnitAlertSuppressArea 0x1bc60: set the
 * under-attack alert cool-down (4000 ticks) of every unit in the 11x11 tiles
 * around a unit, clipped to the 64x64 map.  Called by fn_1bd04.
 *
 * T3 blocker (regalloc): the loops and the pointer walk match (with the byte
 * strides below); the original keeps the unit in edx (`mov edx,eax` at +8) and
 * allocates x to eax and y to esi (`lea eax,[ebx-5]`, `shl eax,2` in place),
 * we allocate x to edx and y to eax, so `lea eax,[edx*4]` replaces the in-place
 * shl and the clip tests use other registers.  Tried: declaration order,
 * locals for the tile (tx/ty), assigning x/y after the declarations, a copy of
 * the unit pointer, w/h as `w = h = 11`, `h = w = 11`, `+=` forms of the clip,
 * pointer vs byte arithmetic.  First difference at +0x8.
 * See docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

#define TILE_X(u) (*(int *)((char *)&(u)->tx - 2) >> 16)
#define TILE_Y(u) (*(int *)((char *)&(u)->ty - 2) >> 16)

/* @0x1bc60 */
void UnitAlertSuppressArea(Unit *u)
{
    int x = TILE_X(u) - 5;
    int y = TILE_Y(u) - 5;
    int w = 11;
    int h = w;
    int r, c;
    Unit **p;

    if (x < 0) {
        w = x + 11;
        x = 0;
    } else if (x + 11 >= 64) {
        w = 64 - x;
    }
    if (y < 0) {
        h = y + 11;
        y = 0;
    } else if (y + 11 >= 64) {
        h = 64 - y;
    }
    p = (Unit **)((char *)object_map + (y << 8) + (x << 2));
    for (r = 0; r < h; r++) {
        for (c = 0; c < w; c++, p++) {
            if (*p != 0)
                (*p)->alert_timer = 4000;
        }
        p = (Unit **)((char *)p + ((64 - w) << 2));
    }
}
