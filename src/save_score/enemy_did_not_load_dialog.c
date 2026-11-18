/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * EnemyDidNotLoadDialog (0x24344), built from C: T3 under Watcom 10.0a.  It
 * was reference C under OW2 (docs/subsystems/save_score.md); split out of
 * src/save_score/link_dialogs_reference.c.
 */
#include "save_score.h"

extern unsigned short net_sync_state[2];   /* 0x5310c */
extern unsigned short evt_pending;         /* 0x516b2 */
extern short game_mode;                    /* 0x59616 */
extern unsigned char net_load_state;       /* 0x5a0a2 */
extern unsigned short screen_mode;         /* 0x593f6 */
extern unsigned short net_event_pending;   /* 0x5a11a */
extern char txt_you_loaded[];              /* 0x57940 */
extern unsigned short ShowMessage(const char *text, unsigned short width,
                                  unsigned short height);  /* 0x1a894 */

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
