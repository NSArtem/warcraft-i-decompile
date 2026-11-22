/* codegen-compiler: 10.0a */
#include "mod_1e380_f1.h"

Unit *FindCustomStartAnchor(unsigned owner)
{
    unsigned type;
    unsigned char *slot;
    unsigned flags;
    int i;

    if (custom_map_group == 2)
        type = (owner == 0 ? scenario_race : scenario_race_enemy) + 2;
    else
        type = (owner == 0 ? scenario_race : scenario_race_enemy) + 0x28;

    i = 0;
    slot = unit_array;
    do {
        flags = *(volatile unsigned short *)(slot + 0x10) & 0x207U;
        if ((unsigned short)flags == 0 && slot[0x1e] == owner &&
            slot[0x1b] == type)
            break;
        ++i;
        slot += 0x5c;
    } while (i < 200);
    return (Unit *)slot;
}
