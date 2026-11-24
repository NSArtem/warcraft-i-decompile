/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
#include "mod_13f60.h"

extern unsigned short dialog_auto_update;
extern unsigned short setup_changed;
extern unsigned char setup_state;
extern unsigned char setup_return_state;
extern void SetRacesDialog(void);
extern void ControlTitleDraw(void);
extern void ScreenUpdate(void);

/* @0x15b30 */
void SetRacesScreen(void)
{
    short saved = screen_mode;

    dialog_auto_update = 0;
    SetRacesDialog();
    if (dat_516ae != 0) {
        do {
            setup_changed = 0;
            screen_mode = (screen_mode == 0);
            ControlTitleDraw();
            SetRacesDialog();
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
