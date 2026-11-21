/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned short load_not_cancelled;
extern unsigned char setup_state;
extern FILE *SaveSlotOpen(int layer, int dialog_id, short *cancelled);
extern void SetGameMode(int mode);

/* @0x15764 */
void LoadGameDialog(void)
{
    short cancelled;

    slot_file = SaveSlotOpen(10, 0x174, &cancelled);
    load_not_cancelled = (unsigned short)(cancelled == 0);
    if (slot_file != 0) {
        if (game_start_mode == 1) {
            SetGameMode(3);
            setup_state = 0x10;
        } else {
            setup_state = 0xe;
        }
    } else {
        setup_state = 0;
    }
    game_start_mode = 0;
}
