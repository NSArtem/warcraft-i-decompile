/* codegen-compiler: 10.0a */
#include "harvest.h"

extern void UnitUpdateGraphicsIndex(Unit *u);

int HarvestDepositCargo(Unit *u)
{
    unsigned char type;
    int first_type;

    type = u->work.target->type;
    first_type = type;
    if (first_type < 0x28 || first_type > 0x29) {
        if ((type & 0xff) < 0x30 || (type & 0xff) > 0x31)
            return 0;
    }

    if (u->harvest_flags & 0x80) {
        player_gold[u->owner] += 100;
        harvested_gold[u->owner] += 100;
    } else if (u->harvest_flags & 0x40) {
        player_lumber[u->owner] += 100;
        harvested_lumber[u->owner] += 100;
    } else {
        goto refresh;
    }
    ++player_score[u->owner];
refresh:
    u->harvest_flags &= 0xdf;
    UnitUpdateGraphicsIndex(u);
    return 1;
}
