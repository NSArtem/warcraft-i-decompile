/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x22ff4  op 0x00: select a movie and open it. */
unsigned short *IntroOpPlayFlic(unsigned short *p)
{
    flic_sel = *p++;
    return IntroBeginFlic(p);
}
