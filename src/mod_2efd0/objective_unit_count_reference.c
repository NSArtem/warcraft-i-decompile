/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* ObjectiveUnitCount (0x2f428): how many of the local player's live units
 * stand on an objective/escape cell (map flag bit 0x20), and whether enough
 * of the special types 0xf/0x12 reached it. */
#include "mod_2efd0.h"

/* @0x2f428 */
int ObjectiveUnitCount(void)
{
    Unit *u;
    unsigned short i;
    int count;
    int special;

    count = 0;
    special = 0;
    u = unit_array;
    for (i = 200; i != 0; i--) {
        if ((u->flags.w & 0x207) == 0 && u->owner == 0 &&
                (map_flags[(u->ty << 6) + u->tx] & 0x20) != 0) {
            count++;
            if (u->type == 0xf || u->type == 0x12)
                special++;
        }
        u++;
    }
    if (scenario_objectives & 4)
        return special >= scenario_objective_count;
    return count;
}
