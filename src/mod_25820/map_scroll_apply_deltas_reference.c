/* codegen-compiler: 10.0a */
#include "war.h"

extern unsigned char map_scroll_cursor_shapes[9]; /* 0x25a00 uses element 1 as its base. */
extern unsigned short map_cursor_shape; /* 0x25a0c loads its low byte. */
extern unsigned short mouse_edge_scroll_requested; /* 0x25a2a stores AX. */
extern short ui_button_bits; /* 0x25a3b compares the word with zero. */
extern void MapScrollFilterMouseDeltas(short *, short *); /* 0x25a36 calls 0x25970. */
extern void MapScrollAddInputDeltas(short *, short *); /* 0x25a4b calls 0x25820. */
extern void MapViewScrollUp(unsigned short); /* 0x25a61 calls 0x125c4. */
extern void MapViewScrollDown(unsigned short); /* 0x25a6f calls 0x12620. */
extern void MapViewScrollLeft(unsigned short); /* 0x25a86 calls 0x12688. */
extern void MapViewScrollRight(unsigned short); /* 0x25a94 calls 0x126e4. */

unsigned int MapScrollApplyDeltas(short dx, short dy)
{
    short y;
    short x;
    long row;
    unsigned short shape;
    unsigned long y_word;
    unsigned long x_word;

    x = dx;
    y = dy;
    row = (*(long *)((char *)&y - 2) >> 16) + 1;
    row *= 3;
    shape = (map_scroll_cursor_shapes + 1)[row + (*(long *)((char *)&x - 2) >> 16)];
    if (shape == 0)
        shape = (unsigned char)map_cursor_shape;

    mouse_edge_scroll_requested = (x != 0 || y != 0);
    MapScrollFilterMouseDeltas(&x, &y);
    if (ui_button_bits == 0)
        MapScrollAddInputDeltas(&x, &y);

    y_word = *(unsigned long *)&y;
    if ((short)y_word < 0)
        MapViewScrollUp((unsigned short)-y_word);
    else if ((short)y_word > 0)
        MapViewScrollDown((unsigned short)y_word);

    x_word = *(unsigned long *)&x;
    if ((short)x_word < 0)
        MapViewScrollLeft((unsigned short)-x_word);
    else if ((short)x_word > 0)
        MapViewScrollRight((unsigned short)x_word);

    return shape;
}
