/* codegen-compiler: 10.0a */
#include "mod_13270.h"

/* 0x137c0/0x137cb load dimensions; 0x13821/0x13824 mark each tile. */
void MarkUnitFootprint(Unit *u)
{
    unsigned short x;
    unsigned short y;
    unsigned short offset;
    unsigned type;
    unsigned short width;
    unsigned short rows;
    unsigned short mask;
    void **obj;
    unsigned short *flags;
    unsigned short cols;

    x = u->tile_x;
    y = u->tile_y;
    offset = y * 64 + x;
    type = u->type;
    width = unit_type_size[type][0];
    rows = unit_type_size[type][1];
    mask = unit_map_class_masks[u->map_class] | 0x0200;
    obj = object_map + offset;
    flags = map_flags + offset;
    offset = 64 - width;

    goto test_row;
row:
    cols = width;
    goto test_col;
col:
    *flags |= mask;
    *obj = u;
    ++flags;
    ++obj;
test_col:
    --cols;
    if (cols != 0xffffU)
        goto col;
    flags += offset;
    obj += offset;
test_row:
    --rows;
    if (rows != 0xffffU)
        goto row;
}
