/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

extern unsigned short map_scroll_x;
extern unsigned short map_scroll_y;

/* @0x19d8c */
void MapViewSave(unsigned short slot)
{
    map_bookmarks[slot].x = map_scroll_x;
    map_bookmarks[slot].y = map_scroll_y;
}
