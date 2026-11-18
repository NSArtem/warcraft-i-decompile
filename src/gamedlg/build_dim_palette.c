/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* Build the 64-entry map that turns the screen's colours into a dark red
 * monochrome image: each palette colour's luminance (the 77/151/28 weights)
 * masked to 6 bits selects the red level, and palette_target becomes a red
 * ramp so the image on screen changes when the palette is uploaded. */
#include <string.h>
#include "gamedlg.h"

/* @0x1a3c0 */
void BuildDimPalette(unsigned char *map)
{
    unsigned short i;
    unsigned char lum;
    unsigned short done;

    memset(map, 0xff, 0x40);
    for (i = 0; i < 0x100; i++) {
        lum = (unsigned char)(palette[i * 3] * 0x4d >> 8);
        lum = (unsigned char)(lum + (palette[i * 3 + 1] * 0x97 >> 8));
        lum = (unsigned char)(lum + (palette[i * 3 + 2] * 0x1c >> 8));
        lum = (unsigned char)(lum & 0x3f);
        palette_target[i * 3 + 2] = 0;
        palette_target[i * 3 + 1] = 0;
        palette_target[i * 3] = lum;
        if (i < 0x80)
            map[lum] = (unsigned char)i;
    }
    PaletteSet(0, 0x100, palette_target);
    /* fill the colours whose luminance no palette entry produces with a
     * neighbouring entry, until the whole ramp is covered */
    do {
        done = 1;
        for (i = 0; i < 0x40; i++) {
            if (map[i] == 0xff) {
                done = 0;
                if (i > 0 && map[i - 1] != 0xff)
                    map[i] = map[i - 1];
                else if (i < 0x3f && map[i + 1] != 0xff)
                    map[i] = map[i + 1];
            }
        }
    } while (!done);
}
