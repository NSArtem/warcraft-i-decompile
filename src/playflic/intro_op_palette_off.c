/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x233b4  op 0x12: stop the decoder from uploading the palette. */
unsigned short *IntroOpPaletteOff(unsigned short *p)
{
    FlicPaletteOff();
    return p;
}
