/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x23c74  Select which credits animation variant runs. */
void CreditsSetAnim(short which)
{
    intro_tick = which ? CreditsTickA : CreditsTickB;
    sound_timer = 1;
}
