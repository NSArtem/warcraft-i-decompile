/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13e60.h"

extern short dat_51530;
extern short game_mode;

/* @0x13e60 */
int DemoIdleTick(void)
{
    if (dialog_modal != 0 && demo_mode == 0) {
        dat_51530--;
        if (dat_51530 == 0) {
            game_mode = 9;
        }
    }
    return 0;
}
