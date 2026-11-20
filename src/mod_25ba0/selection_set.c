/* codegen-compiler: 10.0a */
#include "mod_25ba0_c.h"

extern void *selected_units[2][16];
extern unsigned short player_selection_count[2];
extern void SndUnitSelect(Unit *u);
extern void NetSendSelection(unsigned short count, Unit **units);
extern unsigned short StatusPanelLockGet(void);

/* @0x262a0 */
void SelectionSet(unsigned short count, Unit **list)
{
    unsigned short same;
    unsigned short i;

    if (StatusPanelLockGet() == 0) {
        SndUnitSelect(count == 1 ? list[0] : 0);
        same = (count == player_selection_count[0]);
        if (same != 0) {
            for (i = 0; i < count; i++) {
                if ((void *)list[i] != selected_units[0][i]) {
                    same = 0;
                    break;
                }
            }
        }
        if (same == 0) {
            NetSendSelection(count, list);
        }
    }
}
