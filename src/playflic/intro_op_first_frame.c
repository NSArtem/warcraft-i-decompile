/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x23030  op 0x03: rewind to the first frame and show it. */
unsigned short *IntroOpFirstFrame(unsigned short *p)
{
    if (!FlicRewind())
        return 0;
    frame = 1;
    IntroShowFrame();
    return p;
}
