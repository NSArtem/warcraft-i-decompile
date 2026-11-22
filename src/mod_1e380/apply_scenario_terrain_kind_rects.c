/* codegen-compiler: 10.0a */
#include "mod_1e380_f1.h"

extern void TerrainFillRectMask(unsigned char *rect, unsigned kind);

/* 0x1e38a checks the terminator; 0x1e397 maps byte 4 before the call. */
unsigned char *ApplyScenarioTerrainKindRects(unsigned char *records, const unsigned char *kind_map)
{
    while (*records != 0xff) {
        TerrainFillRectMask(records, kind_map[records[4]]);
        records += 5;
    }
    return records + 2;
}
