void E6WrongCleanup(void);
/* No stack arguments: deliberately return with the wrong ret N. */
#pragma aux E6WrongCleanup = "ret 4" modify exact []
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* E6 negative variant of options_tu.c: intentional callback ABI violation. */
#include "gamedlg.h"


/* @0x1a778 */
int OptionsApplyTimer(struct OptionsParams *p)
{
    unsigned long t = clock();

    if (t > p->next_apply) {
        SndApplyOptions((const int *)p);
        p->next_apply = t + 0x19;
    }
    return 0;
}



/* @0x1a79c */
void OptionsRefresh(struct OptionsParams *p)
{ E6WrongCleanup(); }

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
