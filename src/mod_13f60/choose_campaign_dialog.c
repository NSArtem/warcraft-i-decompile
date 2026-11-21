/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned short scenario_race;
extern unsigned short custom_game;
extern unsigned char setup_state;
extern unsigned char setup_return_state;
extern void SetGameMode(int mode);
extern unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);

/* @0x157e8 */
void ChooseCampaignDialog(void)
{
    unsigned short r;

    custom_game = 0;
    r = DialogRun(0x17d, 0, 0x46, 0x10, 0);
    switch (r) {
    case 0:
        scenario_race = 1;
        SetGameMode(1);
        setup_state = 0x10;
        return;
    case 1:
        scenario_race = 0;
        SetGameMode(1);
        setup_state = 0x10;
        return;
    case 2:
        custom_game = 1;
        setup_return_state = 5;
        setup_state = 5;
        return;
    case 3:
        setup_state = 2;
        break;
    }
}
