/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* Reference C (T4) for 0x1a4b8 DimScreenImage: remap the whole back buffer
 * through the dim map, mark everything dirty and present it, then restore the
 * palette's second half.  T3 is blocked by the loop shape: the original keeps
 * the count in ebx and the pixel scratch in edx and rotates `while (n--)` to a
 * bottom test (`jmp test; ... dec ebx; cmp bx,-1; jne`), 10.0a emits the
 * mirrored allocation and a top test for every spelling tried. */
#include "gamedlg.h"

/* @0x1a4b8 */
void DimScreenImage(void)
{
    unsigned char map[0x40];
    unsigned char *p;
    unsigned short n;
    unsigned char c;

    BuildDimPalette(map);
    p = backbuf_bm.data;
    for (n = 0xfa00; n != 0; n--) {
        c = *p;
        *p = map[palette_target[c * 3]];
        p++;
    }
    dirty_x1 = 0x7fff;
    dirty_y1 = 0x7fff;
    dirty_x2 = -0x8000;
    dirty_y2 = -0x8000;
    dirty_w = 0;
    dirty_h = 0;
    DirtyRectAddBox(0, 0, 0x13f, 0xc7);
    DirtyRectAlignAndPresent();
    PaletteSet(0x80, 0x80, palette);
}
