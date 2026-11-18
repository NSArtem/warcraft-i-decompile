/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The victory screen's box ('You are victorious! Save / Continue'): Save runs
 * the slot list and writes the game, an error message repeats the box, and
 * the box itself closes the victory screen.  Linked games do not save here. */
#include "gamedlg.h"

extern char txt_error_saving[];      /* 0x56bf8, shared by the two dialogs */

/* @0x1aa7c */
void VictoryDialog(void)
{
    short cancelled;
    void *f;

    game_mode = 6;
    if (net_play_flag)
        return;
    ModalScreen(1, 1);
    for (;;) {
        if (DialogRun((unsigned short)(0x1d4 + scenario_race), 0x11, 0x46, 0xa, 0))
            break;
        f = SaveSlotCreate(0xa, (unsigned short)(0x187 + scenario_race), &cancelled);
        if (cancelled)
            continue;
        if (f) {
            SaveWriteImage(f);
            break;
        }
        ShowMessageRace(txt_error_saving, 0x176);
    }
    ModalScreen(0, 1);
}
