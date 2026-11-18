/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The 'Options' page: a copy of the preferences block with the page's two
 * callbacks (refresh, apply timer); Ok copies the values back and applies
 * them, Cancel leaves the preferences alone. */
#include "gamedlg.h"

/* @0x1a800 */
void OptionsDialog(void)
{
    OptionsParams p;

    ModalScreen(1, 1);
    p.prefs = prefs_block;
    p.refresh = OptionsRefresh;
    p.timer = OptionsApplyTimer;
    p.next_apply = clock() + 0x19;
    if (DialogRun((unsigned short)(0x17a + scenario_race), 0x54, 0x14, 0xa,
                  (void **)&p) == 0)
        prefs_block = p.prefs;
    SndApplyOptions((const int *)&prefs_block);
    ModalScreen(0, 1);
}
