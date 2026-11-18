/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x232e8  op 0x0d: stay on this opcode until the movie is aborted. */
unsigned short *IntroOpHold(unsigned short *p)
{
    return p - 1;
}
