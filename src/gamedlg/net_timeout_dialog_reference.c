/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
/* codegen-compiler: 10.0a */
/* The linked game's 'Remote system is not responding!' box (page 0x170, or
 * 0x171 with the Save button while a game is running): Retry returns to the
 * wait loop, Quit leaves the link, and Save runs the save dialog first. */
#include "gamedlg.h"

/* @0x1a9a4 */
unsigned short NetTimeoutDialog(void)
{
    short mode = screen_mode;
    unsigned short saved = layers[0].active;
    int action;

    screen_mode = 1;
    net_play_flag = 0;
    for (;;) {
        ModalScreen(1, 1);
        action = (short)DialogRun(game_mode == 3 ? 0x171 : 0x170, 0x11, 0x46,
                                  8, 0);
        ModalScreen(0, 1);
        if (action == 2) {
            if (GameSaveDialog())
                action = 1;
            else
                continue;
        }
        if (action == 1) {
            NetLinkExit();
            setup_quit = 1;
            game_mode = 4;
            return 1;
        }
        screen_mode = mode;
        net_play_flag = 1;
        layers[0].active = saved;
        return 0;
    }
}
