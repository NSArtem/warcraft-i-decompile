/* codegen-compiler: 10.0a */
#include "mod_25ba0_f1.h"

void SelectionRemoveUnit(Unit *u)
{
    unsigned short player;
    unsigned short saved_player;
    unsigned short i;
    unsigned short count;
    unsigned index;
    unsigned mask;
    unsigned flags;
    Unit *status_unit;

    saved_player = net_event_pending;
    if ((u->selection_flags & 0x2040) != 0) {
        for (player = 0; (index = player) < 2; ++player) {
            mask = player_selection_masks[index];
            flags = u->selection_flags;
            net_event_pending = player;
            if ((flags & mask) != 0) {
                u->selection_flags &= ~mask;
                --player_selection_count[index];
                if (PlaceBoxActive() != 0) {
                    PlaceBoxCancel();
                }
                player = net_event_pending;
                if (player_selection_count[player] == 0 &&
                    (unsigned short)TargetModeIsActive() != 0) {
                    TargetModeExit();
                }
                player = net_event_pending;
                for (i = 0; i < 4; ++i) {
                    if (selected_units[player][i] == u) {
                        selected_units[player][i] = 0;
                    }
                }
                net_event_pending = player;
                if (player == 0) {
                    u->display_type = u->base_type;
                    count = player_selection_count[0];
                    if (count == 0) {
                        selection_local = 1;
                        status_unit = 0;
                        StatusPanelSetUnit(status_unit);
                    } else if (selection_uses_unit_display_type == 0) {
                        SelectionRestoreDisplayTypes();
                        SelectionRefreshStatus();
                    } else if (count == 1) {
                        status_unit = SelectionFirst();
                        StatusPanelSetUnit(status_unit);
                    }
                }
            }
            player = net_event_pending;
        }
    }
    net_event_pending = saved_player;
}
