/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -5r -zp2 */
#include "mod_20c30.h"

/* @0x22a4c */
int PlaceBoxRoad(Point p)
{
    TerrainRoadCell(p.x, p.y, owner_block_mask[net_event_pending]);
    if (net_event_pending == 0) {
        fn_1bd54();
    }
    return 1;
}
