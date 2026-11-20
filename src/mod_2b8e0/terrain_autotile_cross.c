/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

/* @0x2c0bc */
void TerrainAutotileCross(int x, int y, unsigned short flags)
{
    TerrainAutotileCell(x, y, flags);
    TerrainAutotileCell(x - 1, y, 0);
    TerrainAutotileCell(x + 1, y, 0);
    TerrainAutotileCell(x, y - 1, 0);
    TerrainAutotileCell(x, y + 1, 0);
}
