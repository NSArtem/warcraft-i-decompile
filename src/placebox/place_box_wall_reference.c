/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern void UnitStartTraining(Unit *u, unsigned char type);  /* 0x115f4 */

/* @0x22a98 */
int PlaceBoxWall(Unit *worker, Point p)
{
    if (net_event_pending == 0) {
        fn_1bd54();
    }
    TerrainWallCell(p.x, p.y);
    UnitStartTraining(SelectionFirst(0x53), 0x35);
    *(Point *)((char *)worker + 0x42) = p;
    return 0;
}
