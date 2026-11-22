/* codegen-compiler: 10.0a */
#include "mod_1c9c0.h"

void FreeSessionGraphics(void)
{
    unsigned short side_index;
    unsigned short common_index;
    unsigned side_offset;
    unsigned common_offset;
    void *side_sprite;
    void *common_sprite;

    side_index = 0;
    goto side_test;
side_body:
    side_offset <<= 2;
    side_sprite = *(void **)((char *)&session_side_graphics + side_offset);
    if (side_sprite != 0) {
        GdsFree(side_sprite);
        side_sprite = 0;
        *(void **)((char *)&session_side_graphics + side_offset) = side_sprite;
    }
    ++side_index;
side_test:
    side_offset = side_index;
    if ((int)side_offset < 144)
        goto side_body;

    common_index = 0;
    goto common_test;
common_body:
    common_offset <<= 2;
    common_sprite = *(void **)((char *)&session_common_graphics + common_offset);
    if (common_sprite != 0) {
        GdsFree(common_sprite);
        common_sprite = 0;
        *(void **)((char *)&session_common_graphics + common_offset) = common_sprite;
    }
    ++common_index;
common_test:
    common_offset = common_index;
    if ((int)common_offset < 12)
        goto common_body;
}
