/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x23024  op 0x02: end the script with a clean exit request. */
unsigned short *IntroOpQuit(unsigned short *p)
{
    abort_request = 1;
    return 0;
}
