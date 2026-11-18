/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x233c0  op 0x13: upload a palette that is black except colour 0. */
unsigned short *IntroOpBlankPalette(unsigned short *p)
{
    unsigned char pal[0x300];

    memcpy(pal, palette, 0x300);
    memset(pal + 3, 0, 0x2d0);
    VgaSetPaletteRange(pal, 0, 0x100);
    return p;
}
