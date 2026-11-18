/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The 'Save Game' slot list (page 0x187) and the write.  A linked game runs the
 * list once per side (screen_mode flipped), the way the setup screens do, and
 * keeps the handle of the side that was flipped to. */
#include "gamedlg.h"

extern char txt_error_saving[];      /* 0x56bf8, shared by the two dialogs */

/* @0x1abc0 */
unsigned short GameSaveDialog(void)
{
    short cancelled;
    void *f;
    void *f2;

    ModalScreen(1, 1);
    f = SaveSlotCreate(0xa, (unsigned short)(0x187 + scenario_race), &cancelled);
    if (cancelled) {
        ModalScreen(0, 1);
        return 0;
    }
    if (net_play_flag) {
        screen_mode = screen_mode == 0;
        f2 = SaveSlotCreate(0xa, (unsigned short)(0x187 + scenario_race), &cancelled);
        if (screen_mode)
            f = f2;
        screen_mode = screen_mode == 0;
    } else if (f == 0) {
        ShowMessageRace(txt_error_saving, 0x176);
    }
    ModalScreen(0, 1);
    if (f) {
        SaveWriteImage(f);
        return 1;
    }
    return net_play_flag;
}
