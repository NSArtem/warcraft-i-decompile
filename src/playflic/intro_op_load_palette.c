/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x234a0  op 0x16: load a palette resource and set it. */
unsigned short *IntroOpLoadPalette(unsigned short *p)
{
    ResourceBegin(*p++, 0);
    ResourceRead(palette, 0);
    PaletteSet(0, 0x100, palette);
    return p;
}
