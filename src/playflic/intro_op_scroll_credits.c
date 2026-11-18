/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x235ec  op 0x19: keep playing frames while the credits are on screen. */
unsigned short *IntroOpScrollCredits(unsigned short *p)
{
    while (credits_on) {
        IntroTick();
        if (intro_abort)
            break;
        if (frame == flic_frames + 1) {
            if (!IntroShowFirstFrame(p))
                return 0;
        } else if (!IntroNextFrame()) {
            return 0;
        }
    }
    return p;
}
