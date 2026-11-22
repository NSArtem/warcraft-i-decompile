/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_339d0.h"
#include <string.h>

/* @0x339d0 */
void PaletteBeginFade(unsigned char first, unsigned short count, const unsigned char *target_rgb)
{
    unsigned n;
    unsigned off;

    n = count * 3;
    off = first * 3;
    memcpy(palette_base + off, palette_cur + off, n);
    memcpy(palette_target + off, target_rgb, n);
}
