/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The Options page's refresh callback: in a linked game take the option values
 * from the shared globals, and never offer a volume for a driver that is not
 * configured. */
#include "gamedlg.h"

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
