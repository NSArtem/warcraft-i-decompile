/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_32fb0 (0x32fb0..0x33040), DBG style. */
#include <string.h>
#include "graphics.h"

void PaletteLerp(unsigned char first, unsigned char last, short step,
                 short steps);                          /* 0x34c70 */

/* @0x32fb0 */
void PaletteFadeOut(unsigned short steps)
{
    unsigned short i;

    memcpy(palette_base, palette_cur, 0x300);
    memset(palette_target, 0, 0x300);
    for (i = 0; i <= steps; i++)
        PaletteLerp(0, 0xff, i, steps);
    layers[2].active = 1;
    LayerInvalidate(2);
    ScreenUpdate();
    PaletteSet(0, 0x100, palette_base);
    palette_faded = 1;
}
