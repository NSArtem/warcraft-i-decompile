/* codegen-compiler: 10.0a */
#include "mod_1e380_f1.h"

/* 0x1e79b, 0x1e7a2, and 0x1e7a9 chain the returned cursors in EAX. */
unsigned char *LoadScenarioPlacementRecords(unsigned char *records, const unsigned char *value_map)
{
    records = LoadScenarioUnitRecords(records, value_map);
    records = ApplyScenarioTerrainOwnerRects(records, value_map);
    return ApplyScenarioTerrainKindRects(records, value_map);
}
