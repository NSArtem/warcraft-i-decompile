/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned short custom_game;
extern unsigned short connection_type;
extern unsigned short net_modem_link;
extern unsigned char setup_state;
unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);

/* @0x15668 */
void SelectGameTypeDialog(void)
{
    unsigned short r;

    custom_game = 0;
    net_modem_link = 0;
    if (game_start_mode != 0) {
        game_start_mode = 1;
    }
    r = DialogRun(0x17c, 0, 0x46, 0x10, 0);
    switch (r) {
    case 0:
        connection_type = 0;
        setup_state = (game_start_mode == 0) + 3;
        break;
    case 1:
        net_modem_link = 1;
        custom_game = 1;
        connection_type = 1;
        setup_state = 0xa;
        break;
    case 2:
        custom_game = 1;
        connection_type = 2;
        setup_state = 0xc;
        break;
    case 3:
        custom_game = 1;
        connection_type = 3;
        setup_state = 0xd;
        break;
    case 4:
        setup_state = 0;
        break;
    }
    if (game_start_mode != 0 && connection_type != 0) {
        game_start_mode = 2;
    }
}
