/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x2365c  op 0x1b: release all sounds. */
unsigned short *IntroOpFreeSound(unsigned short *p)
{
    SndReleaseAll();
    return p;
}
