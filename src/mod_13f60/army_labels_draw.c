/* codegen-compiler: 10.0a */
#include "graphics.h"
#include "mod_13f60.h"

/* @0x14d68 */
void ArmyLabelsDraw(void)
{
    Bitmap *bm = (Bitmap *)layers[17].data;
    Bitmap *saved = cur_bitmap;
    short a;
    short b;

    if (dat_516ae != 0) {
        if (own_campaign != 0) {
            a = 10;
            b = 0x134;
        } else {
            a = 0x134;
            b = 10;
        }
        cur_bitmap = bm;
        DrawText(a, 0x28, &fmt_decimal[4]);
        DrawText(a, 0x32, &fmt_decimal[8]);
        DrawText(a, 0x3c, &fmt_decimal[0xc]);
        DrawText(b, 0x28, &fmt_decimal[0x10]);
        DrawText(b, 0x32, &fmt_decimal[0x14]);
        DrawText(b, 0x3c, &fmt_decimal[0x18]);
        DrawText(b, 0x46, &fmt_decimal[0x1c]);
        DrawText(b, 0x50, &fmt_decimal[0x20]);
        cur_bitmap = saved;
    }
}
