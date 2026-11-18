/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_32e80 (0x32e80..0x32f10), DBG style. */
#include <string.h>
#include "graphics.h"

void PaletteLerp(unsigned char first, unsigned char last, short step,
                 short steps);                          /* 0x34c70 */
extern unsigned short palette_faded;                    /* 0x55558 */

/* @0x32e80 */
void PaletteFadeIn(unsigned short steps)
{
    unsigned short i;

    memcpy(palette_target, palette_cur, 0x300);
    memset(palette_cur, 0, 0x300);
    PaletteSet(0, 0x100, palette_cur);
    LayerInvalidate(2);
    layers[2].active = 0;
    ScreenUpdate();
    for (i = 0; i <= steps; i++)
        PaletteLerp(0, 0xff, i, steps);
    palette_faded = 0;
}
