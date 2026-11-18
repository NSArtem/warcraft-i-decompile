/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x23054  op 0x04: clear the mode-13 screen. */
unsigned short *IntroOpClearScreen(unsigned short *p)
{
    memset((void *)0xa0000, 0, 0xfa00);
    return p;
}
