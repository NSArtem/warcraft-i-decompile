/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The in-game menu (page 0x172): Save Game, Load Game, Options, Restart
 * scenario, Quit, Continue.  Loops until one of the actions reports that the
 * menu is finished with (a save, a load, the restart question or the quit
 * box), then closes the modal screen. */
#include "gamedlg.h"

/* @0x1ae70 */
void GameMenuDialog(void)
{
    unsigned short action;
    unsigned short done;

    ModalScreen(1, 1);
    done = 0;
    do {
        action = DialogRun((unsigned short)(0x172 + scenario_race), 0x78, 0x14,
                           0xa, 0);
        switch (action) {
        case 0:
            done = GameSaveDialog();
            break;
        case 1:
            done = GameLoadDialog();
            load_not_cancelled = done;
            break;
        case 2:
            OptionsDialog();
            done = 1;
            break;
        case 3:
            if (ShowMessageRace("Are you sure you want to restart the scenario?",
                                0x178)) {
                game_mode = 5;
                done = 1;
            }
            break;
        case 4:
            done = QuitDialog();
            break;
        case 5:
            done = 1;
            break;
        }
    } while (!done);
    ModalScreen(0, 1);
}
