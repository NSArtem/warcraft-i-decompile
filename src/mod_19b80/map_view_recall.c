/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

extern short map_bookmarks_dword_view;
extern void MapViewSetScroll(long x, long y);

/* @0x19d68 */
void MapViewRecall(unsigned short slot)
{
    MapViewSetScroll(*(long *)((char *)&map_bookmarks_dword_view + slot * 4) >> 16, *(long *)((char *)map_bookmarks + slot * 4) >> 16);
}
