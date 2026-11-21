/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned short dialog_modal;
extern unsigned short load_not_cancelled;
extern unsigned short setup_quit;
extern unsigned char setup_state;
extern unsigned short dat_5ab9e;
extern void SetGameMode(int mode);
extern unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);
extern void LayerInvalidate(unsigned char id);
extern void ScreenUpdate(void);

/* @0x15588 */
void MainMenu(void)
{
    unsigned short r;

    LayerInvalidate(0xf);
    dat_5ab9e = 0;
    ScreenUpdate();
    load_not_cancelled = 0;
    dialog_modal = 1;
    setup_quit = 0;
    r = DialogRun(0x105, 0, 0x46, 0x10, 0);
    switch (r) {
    case 0:
        game_start_mode = 0;
        setup_state = 2;
        break;
    case 1:
        game_start_mode = 1;
        setup_state = 2;
        break;
    case 2:
        setup_state = 1;
        break;
    case 3:
        SetGameMode(2);
        setup_state = 0x10;
        break;
    }
    if ((*(long *)((char *)&game_mode - 2) >> 16) == 9) {
        setup_state = 0x10;
    }
    dialog_modal = 0;
}
