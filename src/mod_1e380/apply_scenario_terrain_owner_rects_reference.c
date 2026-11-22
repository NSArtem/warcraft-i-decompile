/* codegen-compiler: 10.0a */
#include "mod_1e380_f1.h"

extern void TerrainFillRectOwnerMask(unsigned char *rect, unsigned owner);

unsigned char *ApplyScenarioTerrainOwnerRects(unsigned char *records, const unsigned char *owner_map)
{
    while (*records != 0xff) {
        TerrainFillRectOwnerMask(records, owner_map[records[4]]);
        records += 5;
    }
    return records + 2;
}
