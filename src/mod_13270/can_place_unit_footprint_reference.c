/* codegen-compiler: 10.0a */
#include "mod_13270.h"

typedef union PlacementY {
    struct {
        unsigned short low;
        short y;
    } words;
    long view;
} PlacementY;

/* 0x139b2–0x139e0 check bounds; 0x139e9–0x139fa select the mask. */
int CanPlaceUnitFootprint(short tile_x, short tile_y, unsigned char type)
{
    unsigned short height;
    unsigned short mask;
    volatile PlacementY coord;
    unsigned short row;
    unsigned short width;
    unsigned short col;
    int index;
    unsigned short *flags;

    coord.words.low = 0;
    coord.words.y = tile_y;
    index = type;
    width = unit_type_size[index][0];
    height = unit_type_size[index][1];
    if (tile_x < 0 || coord.words.y < 0 || tile_x + width > 64 ||
        (coord.view >> 16) + height > 64)
        goto outside;

    if (index <= 31)
        mask = 0x03cc;
    else
        mask = 0x03dc;
    flags = map_flags + (coord.view >> 16) * 64;
    flags += tile_x;

    row = 0;
    if (height == 0)
        goto placeable;
    do {
        col = 0;
        if (width != 0) {
            do {
                if ((unsigned short)tile_x < 64U &&
                    (unsigned short)coord.words.y < 64U &&
                    (*flags & mask) != 0)
                    return 0;
                ++col;
                ++flags;
                ++tile_x;
            } while (col < width);
        }
        tile_x -= width;
        flags += 64 - width;
        ++row;
        ++coord.words.y;
    } while (row < height);
placeable:
    return 1;
outside:
    return 0;
}
