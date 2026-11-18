/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x23cd4  Play movie (index + 0x15) with a fade. */
void IntroPlayMovieB(int index)
{
    flic_sel = index + 0x15;
    IntroRunScript(script_movie, 1);
}
