/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x23394  op 0x11: tick until the sound finishes (abort tested after the
 * tick, unlike op 0x09). */
unsigned short *IntroOpWaitSoundB(unsigned short *p)
{
    while (SndActiveCount()) {
        IntroTick();
        if (intro_abort)
            break;
    }
    return p;
}
