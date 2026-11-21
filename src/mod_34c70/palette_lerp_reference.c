/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 */
#include "mod_34c70_c.h"

extern unsigned char palette_base[768];
extern unsigned char palette_cur[768];
extern unsigned char palette_target[768];
extern void __cdecl VgaSetPaletteRange(const unsigned char *rgb, unsigned first, unsigned count);

/* @0x34c70 */
void PaletteLerp(unsigned char first, unsigned char last, unsigned short step, unsigned short steps)
{
    short i;
    int k;

    for (i = first; i <= last; i++) {
        k = i * 3;
        palette_cur[k] = (unsigned char)(palette_base[k] + ((short)(palette_target[k] - palette_base[k]) * (*(long *)((char *)&step - 2) >> 16)) / (*(long *)((char *)&steps - 2) >> 16));
        palette_cur[k + 1] = (unsigned char)(palette_base[k + 1] + ((short)(palette_target[k + 1] - palette_base[k + 1]) * (*(long *)((char *)&step - 2) >> 16)) / (*(long *)((char *)&steps - 2) >> 16));
        palette_cur[k + 2] = (unsigned char)(palette_base[k + 2] + ((short)(palette_target[k + 2] - palette_base[k + 2]) * (*(long *)((char *)&step - 2) >> 16)) / (*(long *)((char *)&steps - 2) >> 16));
    }
    VgaSetPaletteRange(palette_cur + first * 3, first, (unsigned short)(last - first + 1));
}
