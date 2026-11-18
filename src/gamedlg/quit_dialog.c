/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The 'Quit to DOS or Main Menu?' box (page 0x189): action 0 = DOS (game_mode
 * 2, the main loop's exit), 1 = cancel, 2 = main menu (game_mode 4).  Returns
 * whether the player is leaving the game, in which case the game menu (or the
 * menu command handler) stops. */
#include "gamedlg.h"

/* @0x1ab50 */
unsigned short QuitDialog(void)
{
    int r;

    ModalScreen(1, 1);
    r = (short)DialogRun((unsigned short)(0x189 + scenario_race), 0x11, 0x46, 0xa, 0);
    ModalScreen(0, 1);
    if (r == 0)
        game_mode = 2;
    else if (r == 2)
        game_mode = 4;
    return r != 1;
}
