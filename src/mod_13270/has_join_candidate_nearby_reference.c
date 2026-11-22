/* codegen-compiler: 10.0a */
#include "mod_13270.h"

/* 0x13ad6–0x13aec test the occupant; 0x13b15 writes back object_map. */
int HasJoinCandidateNearby(Unit *u)
{
    void **objects;
    short x;
    short y;
    volatile short row;
    short col;
    Unit *candidate;
    unsigned short flags;
    int result;

    objects = *(void ** volatile *)&object_map;
    x = u->tile_x - 1;
    y = u->tile_y - 1;
    row = 0;
    goto test_row;
next_row:
    col = 0;
    goto test_col;
next_col:
    if ((unsigned short)x >= 64U || (unsigned short)y >= 64U)
        goto advance;
    candidate = objects[y * 64 + x];
    if (candidate == 0)
        goto advance;
    flags = candidate->flags & 0x0207;
    if (flags != 0 || candidate->map_class != 0)
        goto advance;
    result = 1;
    goto done;
advance:
    ++col;
    ++x;
test_col:
    if (col < 3)
        goto next_col;
    x -= 3;
    ++row;
    ++y;
test_row:
    if (row < 3)
        goto next_row;
    result = 0;
done:
    *(void ** volatile *)&object_map = objects;
    return result;
}
