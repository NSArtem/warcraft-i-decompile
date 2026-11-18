/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x2315c  op 0x07: play a sound. */
unsigned short *IntroOpPlaySound(unsigned short *p)
{
    SndPlay(*p++);
    return p;
}
