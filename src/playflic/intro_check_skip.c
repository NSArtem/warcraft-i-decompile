/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x22e60  Installed in the three event handler slots: any mouse button
 * event (type & 0x380 == 0) or any ASCII key (the high byte of the translated
 * key is 0) aborts the movie. */
void IntroCheckSkip(Event *ev)
{
    if ((ev->type & 0x380) == 0 || ((unsigned char *)ev)[0xb] == 0)
        intro_abort = 1;
}
