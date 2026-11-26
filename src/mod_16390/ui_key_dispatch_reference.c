/* codegen-compiler: 10.0a */
#include "mod_16390.h"

extern void (*event_handlers[10])(Event *ev);

/* @0x182e4 */
void UiKeyDispatch(Event *ev)
{
    unsigned code;

    if (ev->mods & 8) {
        ev->mods = (ev->mods & 0xf3) | 4;
    }
    code = (ev->mods << 8) + ev->scan;
    if (ui_button_bits == 0) {
        code &= 0xffff;
        if (code == 0x29) {
            /* int3 debug break omitted */
        } else if (code == 0x432) {
            if (ui_net_forward == 0 || screen_mode != 0) {
                SndToggleMusic();
                DemoIdleTimerReset();
                return;
            }
        } else if (code == 0x41f) {
            if (ui_net_forward == 0 || screen_mode != 0) {
                SndToggleSfx();
                DemoIdleTimerReset();
                return;
            }
        } else if (event_handlers[0] != 0) {
            event_handlers[0](ev);
        }
    }
    DemoIdleTimerReset();
}
