/* codegen-compiler: 10.0a */
/* mod_1b800.  SndUnitSelect 0x1ba24: the voice of a newly selected unit.
 * Player units only; repeated clicks on the same unit walk through the
 * 'what?' voices and then the annoyed ones.  Called by SelectionSet 0x262a0.
 * See docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1ba24 */
void SndUnitSelect(Unit *u)
{
    unsigned short id;

    if (u == 0 || u->owner != 0) {
        snd_last_selected = 0;
        snd_select_clicks = 0;
        return;
    }
    if (u == snd_last_selected && snd_select_cooldown != 0)
        return;
    snd_select_cooldown = 0x3c;
    if (u != snd_last_selected) {
        snd_last_selected = u;
        snd_select_clicks = 0;
    }
    if (u->type >= 0x2e && u->type <= 0x2f) {
        id = 0x2d;
    } else if (u->type >= 0x24 && u->type <= 0x25) {
        id = 0x2e;
    } else if (u->type >= 0x2c && u->type <= 0x2d) {
        id = 0x2f;
    } else if (u->type >= 0x13 || (u->type >= 4 && u->type <= 5)) {
        id = 0x21;
    } else if (snd_select_clicks < 2) {
        id = 3 + rand() % 5;
        snd_select_clicks++;
    } else {
        id = snd_select_clicks + 6;
        snd_select_clicks++;
        if (snd_select_clicks >= 5) {
            snd_select_clicks = 0;
            snd_select_cooldown = 0x78;
        }
    }
    SndEvent(id, 0);
}
