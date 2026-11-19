/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* MissionToMenu (0x2f748): leave the mission to the main menu (game_mode 4). */
#include "mod_2efd0.h"

/* @0x2f748 */
void MissionToMenu(void)
{
    game_mode = 4;
}
