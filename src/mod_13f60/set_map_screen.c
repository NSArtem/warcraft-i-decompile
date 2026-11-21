/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned short dialog_auto_update;
extern unsigned short setup_changed;
extern unsigned char setup_state;
extern unsigned char setup_return_state;
void SetMapDialog(void);
void ControlTitleDraw(void);
void ScreenUpdate(void);

/* @0x15bc0 */
void SetMapScreen(void)
{
    short saved;

    saved = screen_mode;
    dialog_auto_update = 0;
    SetMapDialog();
    if (dat_516ae != 0) {
        do {
            setup_changed = 0;
            screen_mode = (screen_mode == 0);
            ControlTitleDraw();
            SetMapDialog();
        } while (setup_changed != 0);
        if (saved != screen_mode) {
            screen_mode = (screen_mode == 0);
            ControlTitleDraw();
        }
    }
    dialog_auto_update = 1;
    ScreenUpdate();
    setup_state = setup_return_state;
}
