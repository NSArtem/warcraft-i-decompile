/* codegen-compiler: 10.0a */
#include "mod_25ba0_f1.h"

void SelectionRefreshStatus(void)
{
    Unit *u;
    unsigned short use_type;
    unsigned short local;
    unsigned short zero;
    unsigned short same_type;

    u = SelectionFirst();
    if (u == 0) {
        return;
    }
    selection_first_display_type = u->display_type;
    selection_uses_unit_display_type =
        (unsigned short)(scenario_race + 0x3b != selection_first_display_type);
    local = (u->owner == 0 && type_is_creature[u->base_type] != 0) ? 1 : 0;
    selection_local = local;
    zero = 0;
    for (;;) {
        u = SelectionNext();
        if (u == 0) {
            break;
        }
        use_type = selection_uses_unit_display_type;
        if (zero == use_type) {
            break;
        }
        if (zero != use_type) {
            same_type = (unsigned short)(selection_first_display_type == u->display_type);
            selection_uses_unit_display_type = same_type;
        }
    }
    if (selection_uses_unit_display_type == 0) {
        SelectionSetDisplayType((unsigned short)(scenario_race + 0x3b));
    }
    StatusPanelSetUnit(SelectionFirst());
}
