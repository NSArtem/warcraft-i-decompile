/* codegen-flags: -s -ot -ol -4r -zp2
 * REFERENCE C for the two SAVE.C error dialogs of the two-player load path
 * (0x24304 GamesDifferDialog, 0x24344 EnemyDidNotLoadDialog).  Not built:
 * OW2 keeps the saved screen-mode word in another register (see the
 * t3_blocker in analysis/symbols/save_score.toml); verified as T4 against
 * the original with wc1.cemu (tests/test_save_score.py).
 *
 * ShowMessage (0x1a894) is the modal message box: watcall
 * (text, 0x176, 10).  It lives outside this area and has no symbol entry
 * yet, so the T4 test supplies its address through cemu's extra= map.
 */
#include "save_score.h"

extern unsigned short net_sync_state[2];   /* 0x5310c */
extern unsigned short evt_pending;         /* 0x516b2 */
extern short game_mode;                    /* 0x59616 */
extern unsigned char net_load_state;       /* 0x5a0a2 */
extern unsigned short screen_mode;         /* 0x593f6 */
extern unsigned short own_campaign;        /* 0x52584 */
extern unsigned short net_event_pending;   /* 0x5a11a */
extern char txt_games_differ[];            /* 0x57920 */
extern char txt_you_loaded[];              /* 0x57940 */

extern void ShowMessage(const char *txt, int width, int height);  /* 0x1a894 */

/* @0x24304  show "the two games did not match": force our campaign word
 * into the screen-mode slot while the message is up, then restore it and
 * clear the pending-event word. */
void GamesDifferDialog(void)
{
    unsigned short save = screen_mode;

    screen_mode = own_campaign;
    ShowMessage(txt_games_differ, 0x176, 10);
    screen_mode = save;
    evt_pending = 0;
}

/* @0x24344  "your enemy did not load": in handshake phase 1 (the high word
 * of net_sync_state) it shows the message with the screen mode forced to 1
 * and drops the load state back to 2; otherwise it only reacts when exactly
 * one link event is pending, switching the game mode word to 4. */
void EnemyDidNotLoadDialog(void)
{
    unsigned short save;

    if ((int)(*(unsigned long *)net_sync_state) >> 16 != 1) {
        unsigned pending = net_event_pending;

        if (pending == 1 && evt_pending != 0) {
            game_mode = 4;
            evt_pending = 0;
        }
        return;
    }
    save = screen_mode;
    screen_mode = 1;
    ShowMessage(txt_you_loaded, 0x176, 10);
    screen_mode = save;
    net_load_state = 2;
    evt_pending = 0;
}
