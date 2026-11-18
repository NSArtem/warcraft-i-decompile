/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x2322c  op 0x0b: stop the credits animation. */
unsigned short *IntroOpStopTick(unsigned short *p)
{
    intro_tick = 0;
    return p;
}
