/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x22c50
 * One animation tick: pump one event (0x184cc dispatches it through the
 * handler table at 0x51770, which is where the skip check arrives) and then
 * run the installed credits animation tick, if any.
 */
void IntroTick(void)
{
    UiEventPump();
    if (intro_tick)
        intro_tick();
}
