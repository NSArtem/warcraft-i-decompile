/* codegen-compiler: 10.0a */
#include "mod_25ba0_f1.h"

void SelectionClearCurrent(void)
{
    unsigned short player;
    unsigned short i;
    unsigned index;
    unsigned row;
    unsigned offset;
    Unit *u;

    player = net_event_pending;
    if (player == 0) {
        StatusPanelSetUnit(0);
        selection_local = 1;
    }
    player = net_event_pending;
    player_selection_count[player] = 0;
    for (i = 0; (index = i) < 4; ++i) {
        row = player;
        offset = row << 4;
        index <<= 2;
        offset += index;
        u = (Unit *)*(void **)((char *)selected_units + offset);
        if (u != 0) {
            *(void **)((char *)selected_units + offset) = 0;
            u->selection_flags &= ~player_selection_masks[row];
            u->display_type = u->base_type;
        }
    }
    net_event_pending = player;
}
