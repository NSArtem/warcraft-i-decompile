/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned short setup_quit;
extern char setup_state;
extern char setup_return_state;
extern void ControlTitleDraw(void);
extern void SetGameMode(int mode);
extern unsigned short DialogRun(unsigned short id, short x, short y, unsigned short layer, void **params);
extern void NetLinkExit(void);

/* @0x15898 */
void CustomGameMenu(void)
{
    unsigned short r;
    int id;

    if (setup_quit != 0) {
        setup_state = 0;
        return;
    }
    ControlTitleDraw();
    id = dat_516ae ? 0x186 : 0x17f;
    r = DialogRun((unsigned short)id, 0, 0x46, 0x10, 0);
    switch (r) {
    case 0:
        if (dat_516ae == 0 || setup_return_state == 6) {
            SetGameMode(1);
            setup_state = 0x10;
            return;
        }
        screen_mode = (screen_mode == 0);
        setup_return_state = 6;
        setup_state = 6;
        return;
    case 1:
        if (dat_516ae != 0 || setup_quit != 0) {
            NetLinkExit();
            setup_state = 0;
            return;
        }
        setup_state = 4;
        return;
    case 2:
        setup_state = 8;
        return;
    case 3:
        setup_state = 7;
        return;
    case 4:
        setup_state = 9;
        return;
    }
}
