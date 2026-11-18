/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x23170  op 0x08: keep the movie running while the sound plays. */
unsigned short *IntroOpSyncSound(unsigned short *p)
{
    while (SndActiveCount()) {
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
