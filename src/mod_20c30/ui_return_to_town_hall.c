/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern char str_town_hall_destroyed[];
extern void *player_town_hall[5];
extern unsigned short pending_order;
extern void IssueOrderAt(short x, short y, Unit *target);

/* @0x21130 */
void UiReturnToTownHall(void)
{
    if (player_town_hall[0] == 0) {
        fn_19f70(str_town_hall_destroyed, 0x24);
        return;
    }
    pending_order = 0xb;
    IssueOrderAt(0, 0, (Unit *)player_town_hall[0]);
}
