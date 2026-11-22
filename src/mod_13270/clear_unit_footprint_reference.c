/* codegen-compiler: 10.0a */
#include "mod_13270.h"

/* 0x138ca–0x138d5 form the keep mask; 0x138ec/0x138ef clear each tile. */
void ClearUnitFootprint(Unit *u)
{
    unsigned short x;
    unsigned short offset;
    unsigned type;
    unsigned short width;
    unsigned short rows;
    void **obj;
    unsigned short *flags;
    unsigned short mask;
    unsigned short cols;

    x = u->tile_x;
    offset = u->tile_y;
    offset = offset * 64 + x;
    type = u->type;
    width = unit_type_size[type][0];
    rows = unit_type_size[type][1];
    obj = object_map + offset;
    flags = map_flags + offset;
    offset = 64 - width;
    mask = unit_map_class_masks[u->map_class];
    mask |= 0x0200;
    mask = ~mask;

    --rows;
    if (rows == 0xffffU)
        return;
row:
    cols = width;
    goto test_col;
col:
    *flags &= mask;
    *obj = 0;
    ++flags;
    ++obj;
test_col:
    --cols;
    if (cols != 0xffffU)
        goto col;
    flags += offset;
    obj += offset;
    --rows;
    if (rows != 0xffffU)
        goto row;
}
