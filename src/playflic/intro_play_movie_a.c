/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x23cb4  Play movie (index + 9) with a fade. */
void IntroPlayMovieA(int index)
{
    flic_sel = index + 9;
    IntroRunScript(script_movie, 1);
}
