/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* MissionDefeat (0x2f73c): the defeat condition's action - install
 * DefeatDialog (game_mode 7) as the pending mission-end action. */
#include "mod_2efd0.h"

/* @0x2f73c */
void MissionDefeat(void)
{
    end_screen_action = DefeatDialog;
}
