/* codegen-compiler: 10.0a */
#include "mod_25ba0_f1.h"

void SelectionRebuildFromUnitFlags(void)
{
    Unit *units[4];
    Unit *u;
    unsigned short player = *(volatile unsigned short *)&net_event_pending;
    unsigned short count;
    unsigned short remaining;
    unsigned mask;

    selection_local = 1;
    memset(selected_units, 0, sizeof(selected_units));
    player_selection_count[1] = 0;
    player_selection_count[0] = 0;
    for (player = 0; player < 2; ++player) {
        count = 0;
        u = (Unit *)unit_array;
        remaining = 200;
        goto scan_test;
        do {
            mask = player_selection_masks[player];
            if (u->selection_flags & mask) {
                units[count] = u;
                ++count;
            }
            ++u;
scan_test:
            ;
        } while (--remaining != (unsigned short)-1);
        net_event_pending = player;
        fn_25f9c(count, units);
        player = net_event_pending;
    }
    player = 0;
    net_event_pending = player;
}
