/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x2300c  op 0x01: close the movie. */
unsigned short *IntroOpEndFlic(unsigned short *p)
{
    flic_open = 0;
    FlicClose();
    return p;
}
