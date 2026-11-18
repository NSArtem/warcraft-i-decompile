/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for the selection-driven button gates of STATUS.C (0x27b20..
 * 0x295d0): CanHarvest 0x27b28, CanReturnGoods 0x27b68 and SelectionIsWorkers
 * 0x28074.  T4 material (see the t3_blocker of each entry); not built. */
#include "status.h"

/* 0x27b28 - the "harvest lumber/mine gold" button (0x53e38/0x53ec4): every
 * selected unit must be a peasant/peon (type 2/3) and must not be carrying
 * (unit+0x49 bit 0x20 clear). */
unsigned short CanHarvest(void)
{
    Unit *u;
    unsigned long type;

    u = SelectionFirst();
    if (u != 0) {
        do {
            type = u->type;
            if (type < 2 || type > 3)
                return 0;
            if (u->work.b.state & 0x20)
                return 0;
            u = SelectionNext();
        } while (u != 0);
    }
    return 1;
}

/* 0x27b68 - the "return goods to town hall" button (0x53e4c/0x53ed8): one
 * unit selected, carrying, and the player still owns a town hall. */
unsigned short CanReturnGoods(void)
{
    if (player_selection_count[0] > 1)
        return 0;
    if (!(status_unit->work.b.state & 0x20))
        return 0;
    if (player_town_hall[0] == 0)
        return 0;
    return 1;
}

/* 0x28074 - the "attack" button of the two 5-button cards 0x54950/0x549b4
 * (types 0x3b/0x3c): available while no selected unit is a worker (peasants
 * and peons cannot attack).  The original spans 0x28074..0x280a2; code
 * discovery splits it at the shared `return 0` block (0x28090) and at the loop
 * continuation (0x28093). */
unsigned short SelectionHasNoWorkers(void)
{
    Unit *u;
    unsigned long type;

    u = SelectionFirst();
    while (u != 0) {
        type = u->type;
        if (type >= 2 && type <= 3)
            return 0;
        u = SelectionNext();
    }
    return 1;
}
