/* codegen-compiler: 10.0a */
#include "mod_1af20.h"

extern int fn_2b308(void); /* 0x1b5e8: return tested in ax. */
extern unsigned short PlaceBoxActive(void); /* 0x1b5f6: return tested in ax. */
extern void NetSendTargetCancel(void); /* 0x1b5f0: nonzero target-state branch. */
extern void PlaceBoxPress(void); /* 0x1b5fe: nonzero placement-state branch. */
extern void fn_20c4c(int arg); /* 0x1b604..0x1b606: tail jump with eax = 0. */

void GameScreenCancelOrPlace(void)
{
    if ((short)fn_2b308() != 0) {
        NetSendTargetCancel();
    } else if (PlaceBoxActive() != 0) {
        PlaceBoxPress();
    } else {
        fn_20c4c(0);
    }
}
