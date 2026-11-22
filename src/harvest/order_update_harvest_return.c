/* codegen-compiler: 10.0a */
#include "harvest.h"

extern int UnitRetaliate(Unit *u, int is_human);
extern int fn_2eefc(Unit *u, void (*cb)(Unit *), int flag);

#pragma aux OrderUpdateHarvestReturn modify exact [eax gs]

int OrderUpdateHarvestReturn(Unit *u, int is_human)
{
    if ((short)UnitRetaliate(u, is_human) == 0 &&
        (short)fn_2eefc(u, UiOrderSetNext3_11, 1) == 0)
        HarvestQueueBuildingEntry(u);
    return 1;
}
