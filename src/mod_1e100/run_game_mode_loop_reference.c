/* codegen-compiler: 10.0a */
#include "mod_1e100.h"
#include <stdio.h>

extern void SetCursorShape(unsigned char id);
extern void DemoIdleTimerReset(void);
extern void DemoRun(void);
extern void UiInputInit(void);
extern void OutroPlay(void);
extern void GameInitSession(unsigned char *save_pos);
extern void GameRunSession(void);
extern void GameShutdownSession(void);
extern void fn_1c300(void);
extern void fn_1da34(void);
extern void ShowSplashScreen(void);
extern void PacketTick(void);
extern void NetSendControlPacket(unsigned short id);
extern void IntroPlay(void);
extern unsigned char *SaveLoadImage(FILE *fp);
extern void RunSetupMenu(void);
extern void EndScreen(void);
extern void LayerInvalidate(unsigned char id);
extern void ScreenUpdate(void);
extern void exit(int status);

void RunGameModeLoop(void)
{
    unsigned long zero;
    int setup_mode;
    unsigned char *save_pos;
    unsigned char *pending;
    unsigned char *loaded;
    FILE *file;
    unsigned short net;

    archive_version = 0x18;
    archive_version_error = archive_version_error_message;
    zero = 0;
    pending_save_image = (unsigned char *)zero;
    slot_file = (void *)zero;
    game_mode = 8;
    fn_1da34();
    UiInputInit();
    setup_mode = 4;

    for (;;) {
        SetCursorShape(7);
        LayerInvalidate((unsigned char)zero);
        ScreenUpdate();

        switch (game_mode) {
        case 3:
            save_pos = (unsigned char *)zero;
            pending = pending_save_image;
            if ((unsigned char *)zero != pending) {
                save_pos = pending;
                pending_save_image = (unsigned char *)zero;
                goto start_session;
            }
            file = (FILE *)slot_file;
            if ((FILE *)pending != file) {
                loaded = SaveLoadImage(file);
                save_pos = loaded;
                fclose((FILE *)slot_file);
                slot_file = pending;
                if (loaded != 0)
                    goto start_session;
                game_mode = (short)setup_mode;
                break;
            }
            if ((unsigned short)(unsigned long)pending == custom_game) {
                fn_1c300();
                goto start_session;
            }
            NetSendControlPacket(0x0d);
            PacketTick();
            if ((*(volatile long *)&game_mode_dword_low >> 16) == 3)
                PacketTick();
            if ((*(volatile long *)&game_mode_dword_low >> 16) != 3)
                break;
        start_session:
            load_not_cancelled = (unsigned short)zero;
            evt_pending = (unsigned short)zero;
            GameInitSession(save_pos);
            GameRunSession();
            GameShutdownSession();
            break;

        case 1:
            InitNewCampaign();
            /* Fall through. */
        case 5:
            game_mode = 3;
            break;

        case 0:
            IntroPlay();
            game_mode = (short)setup_mode;
            break;

        case 4:
            DemoIdleTimerReset();
            demo_mode = (unsigned short)zero;
            RunSetupMenu();
            break;

        case 6:
        case 7:
            EndScreen();
            net = net_play_flag;
            if ((unsigned short)zero == net && net == setup_quit)
                goto check_end_mode;
            game_mode = (short)setup_mode;
            break;
        check_end_mode:
            if ((*(volatile long *)&game_mode_dword_low >> 16) != 7)
                goto copy_scenario;
        next_scenario:
            game_mode = 5;
            break;
        copy_scenario:
            scenario_number = map_scroll_x_low_word;
            if (*(volatile unsigned short *)&scenario_number != 0xffffU)
                goto next_scenario;
            game_mode = (unsigned short)zero != custom_game ? setup_mode : 10;
            break;

        case 10:
            OutroPlay();
            game_mode = (short)setup_mode;
            break;

        case 8:
            ShowSplashScreen();
            game_mode = (short)zero != preferences_load_failed ? (int)zero : setup_mode;
            break;

        case 9:
            DemoRun();
            break;

        case 2:
        default:
            exit((int)zero);
            break;
        }
    }
}
