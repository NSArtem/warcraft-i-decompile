/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The 'Load Game' slot list (page 0x174): opening a slot stores its stream in
 * slot_file and sets game_mode 5, which the main loop turns into the actual
 * game start.  A linked game runs the list once per side. */
#include "gamedlg.h"

/* @0x1accc */
unsigned short GameLoadDialog(void)
{
    short cancelled;
    void *f;

    ModalScreen(1, 1);
    f = SaveSlotOpen(0xa, 0x174 + scenario_race, &cancelled);
    slot_file = f;
    ModalScreen(0, 1);
    if (cancelled)
        return 0;
    if (net_play_flag == 0) {
        if (slot_file == 0)
            return 0;
        game_mode = 5;
        return 1;
    }
    screen_mode = screen_mode == 0;
    ModalScreen(1, 1);
    f = SaveSlotOpen(0xa, 0x174 + scenario_race, &cancelled);
    if (screen_mode)
        slot_file = f;
    ModalScreen(0, 1);
    screen_mode = screen_mode == 0;
    if (cancelled == 0) {
        game_mode = 5;
        return 1;
    }
    if (slot_file) {
        fclose(slot_file);
        slot_file = 0;
    }
    return 0;
}
