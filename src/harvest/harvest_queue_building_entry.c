/* codegen-compiler: 10.0a */
#include "harvest.h"

extern unsigned char fn_1def0(Unit *u);
extern void SelectionRemoveUnit(Unit *u);
extern void UnitSetNextOrder(void *u, unsigned char order);

void HarvestQueueBuildingEntry(Unit *u)
{
    unsigned char type;

    SelectionRemoveUnit(u);
    UnitSetNextOrder(u, 0x0c);
    u->direction = fn_1def0(u);
    u->harvest_flags &= 0xef;
    type = u->work.target->type;
    if (type >= 0x30 && type <= 0x31)
        u->harvest_flags |= 4;
}
