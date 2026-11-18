/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x22cfc  Rewind and show the first frame; p is the opcode that follows. */
unsigned short *IntroShowFirstFrame(unsigned short *p)
{
    if (!FlicRestart())
        return 0;
    frame = 2;
    IntroShowFrame();
    return p;
}
