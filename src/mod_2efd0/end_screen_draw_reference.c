/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndScreenDraw (0x2f938): redraw the 13 numbers of the win/lose screen into
 * the transparent text bitmap (layer 15); the last one (the score) is
 * centred. */
#include "mod_2efd0.h"

/* @0x2f938 */
void EndScreenDraw(void)
{
    unsigned short i;

    cur_bitmap = &end_text_bm;
    BitmapClear(0);
    for (i = 0; i < 13; i++) {
        if (i == 12)
            DrawNumberCentre(end_value_x[i], end_value_y[i],
                             end_screen_value[i]);
        else
            DrawNumberRight(end_value_x[i], end_value_y[i],
                            end_screen_value[i]);
    }
    LayerInvalidate(0xf);
}
