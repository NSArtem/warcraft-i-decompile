/* codegen-compiler: 10.0a */
#include "mod_1af20.h"

extern void MapViewSetScroll(short x, short y); /* 0x1b126: jump to 0x1274c. */

void MapCenterOnTile(short x, short y)
{
    x -= 7;
    y -= 5;
    MapViewSetScroll(x, y);
}
