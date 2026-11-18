/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Palette hardware access, palette upload and colour cycling (modules
 * mod_33150, mod_331be, mod_33220).  Reference C: the DAC port writes are
 * inline asm in the original (two jmp delays per byte) and the cycle code
 * differs in register allocation, so these are difftested in
 * tests/test_graphics_lib.py.
 */
#include <string.h>
#include "graphics.h"

#pragma aux out_port = "out dx,al" parm [dx] [al] modify exact [eax edx];

void __cdecl FatalError(const char *fmt, ...);          /* 0x30bf0 */
extern const char vidinicy1_msg[];                      /* 0x57eb8 */

/* @0x33150 */
void PaletteSet(unsigned char first, unsigned short count, const unsigned char *rgb)
{
    unsigned off = first * 3;

    memcpy(palette_base + off, rgb + off, (unsigned)count * 3);
    memcpy(palette_cur + off, rgb + off, (unsigned)count * 3);
    VgaSetPaletteRange(rgb + off, first, count);
}

/* @0x331be */
void __cdecl VgaSetPaletteRange(const unsigned char *rgb, unsigned first, unsigned count)
{
    unsigned i;

    out_port(0x3c8, first);
    for (i = 0; i < count * 3; i++)
        out_port(0x3c9, rgb[i]);
}

/* @0x33220 */
void PaletteCycleStepList(unsigned id)
{
    unsigned char *c = palette_cycles + id * 12;
    unsigned char cur;
    unsigned i;

    if (c[4] > c[6]) {
        FatalError(vidinicy1_msg);
        return;
    }
    if (++c[5] == c[11])
        c[5] = 0;
    cur = c[5];
    for (i = c[4]; i <= c[6]; i++) {
        const unsigned char *src = *(const unsigned char **)(c + 7) + cur * 3;
        palette_cur[i * 3 + 0] = src[0];
        palette_cur[i * 3 + 1] = src[1];
        palette_cur[i * 3 + 2] = src[2];
        if (++cur == c[11])
            cur = 0;
    }
}

/* @0x33324 */
void PaletteCyclesUpdate(void)
{
    unsigned short i;
    unsigned short first_min = 0x100, last_max = 0;

    for (i = 0; i < 16; i++) {
        unsigned char *c = palette_cycles + i * 12;

        if (*(unsigned short *)c == 0)
            continue;
        if (--c[3] != 0)
            continue;
        c[3] = c[2];
        if (*(void **)(c + 7) != 0) {
            PaletteCycleStepList(i);
        } else {
            unsigned char first = c[4], last = c[6];
            unsigned char tmp[3];

            tmp[0] = palette_cur[last * 3 + 0];
            tmp[1] = palette_cur[last * 3 + 1];
            tmp[2] = palette_cur[last * 3 + 2];
            if (first <= last) {
                memmove(palette_cur + (first + 1) * 3, palette_cur + first * 3,
                        (last - first) * 3);
            } else {
                memmove(palette_cur + last * 3, palette_cur + (last + 1) * 3,
                        (first - last) * 3);
            }
            palette_cur[first * 3 + 0] = tmp[0];
            palette_cur[first * 3 + 1] = tmp[1];
            palette_cur[first * 3 + 2] = tmp[2];
        }
        if (last_max < c[6]) last_max = c[6];
        if (first_min > c[4]) first_min = c[4];
    }
    if (first_min <= last_max)
        VgaSetPaletteRange(palette_cur + first_min * 3, first_min,
                           last_max - first_min + 1);
}
