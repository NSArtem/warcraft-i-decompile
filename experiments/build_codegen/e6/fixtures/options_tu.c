/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* E6 consolidation; bodies copied unchanged from src/gamedlg. */
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
{
    if (net_event_pending) {
        p->prefs.music_volume = opt_music_volume;
        p->prefs.sfx_volume = opt_sfx_volume;
        p->prefs.mouse_scroll = opt_mouse_scroll;
        p->prefs.key_scroll = opt_key_scroll;
    }
    if (cfg_mdi_driver == 0xffff)
        p->prefs.music_volume = 0;
    if (cfg_dig_driver == 0xffff)
        p->prefs.sfx_volume = 0;
}



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
