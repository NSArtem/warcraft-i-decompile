/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * GamesDifferDialog (0x24304), built from C: T3 under Watcom 10.0a.  It was
 * reference C under OW2 (docs/subsystems/save_score.md); split out of
 * src/save_score/link_dialogs_reference.c because the neighbour
 * EnemyDidNotLoadDialog 0x24344 is now built from its own file and
 * NotValidTwoPlayerDialog 0x243c4 is still reference C.
 */
#include "save_score.h"

extern unsigned short evt_pending;         /* 0x516b2 */
extern unsigned short screen_mode;         /* 0x593f6 */
extern unsigned short own_campaign;        /* 0x52584 */
extern char txt_games_differ[];            /* 0x57920 */
extern unsigned short ShowMessage(const char *text, unsigned short width,
                                  unsigned short height);  /* 0x1a894 */

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
