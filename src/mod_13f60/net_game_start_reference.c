/* codegen-compiler: 10.0a */
#include "mod_13f60.h"
#include <string.h>

typedef struct Army13 { unsigned long v[0x13]; } Army13;
typedef struct Map0b { unsigned long v[0xb]; } Map0b;

extern unsigned short scenario_race;
extern unsigned short scenario_race_enemy;
extern union { unsigned long w; unsigned char b[4]; } cheat_flags;
extern unsigned long map_choice_params[0xb];
extern unsigned long army_setup[0x13];
extern unsigned short evt_pending;
extern const char dat_51701[];
extern unsigned short net_play_flag;
extern unsigned char setup_state;
extern unsigned char setup_return_state;
extern char net_error_text[0x38];
extern unsigned short key_down_table[128];
extern unsigned long cd_1461c[0x13];
extern unsigned long cd_145f0[0xb];
unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);
void SetGameMode(int mode);
short NetLinkStart(void);
void NetLinkExit(void);
int FileClose(FILE *fp);
void fn_15230(void);

/* @0x160f0 */
void NetGameStart(void)
{
    void (*cb)(void);

    cb = fn_15230;
    if (game_start_mode != 0) {
        setup_state = 3;
        return;
    }
    *(Army13 *)army_setup = *(Army13 *)cd_1461c;
    *(Map0b *)map_choice_params = *(Map0b *)cd_145f0;
    strcpy(net_error_text, dat_51701);
    if (NetLinkStart() == 0) {
        if (key_down_table[1] != 0 || key_down_table[46] != 0) {
            setup_state = 0;
        } else {
            setup_state = 0xf;
        }
        NetLinkExit();
        return;
    }
    dat_516ae = 0;
    if (DialogRun(0x18d, 0, 0x46, 0x10, (void **)&cb) != 0) {
        setup_state = 0;
    } else if (dat_516ae != 0) {
        setup_return_state = 5;
        setup_state = 5;
    } else {
        setup_state = 0xf;
    }
    if (setup_state != 5) {
        NetLinkExit();
        if (slot_file != 0) {
            FileClose((FILE *)slot_file);
            slot_file = 0;
        }
        return;
    }
    net_play_flag = 1;
    cheat_flags.w = 0;
    if (own_campaign != 0) {
        scenario_race = 1;
        scenario_race_enemy = 0;
    } else {
        scenario_race = 0;
        scenario_race_enemy = 1;
    }
    SetGameMode(3);
    setup_state = 0x10;
    screen_mode = own_campaign;
    evt_pending = 1;
}
