/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module PLAYFLIC.C (0x22c50..0x23d10), game code, "OPT" style.
 * See docs/subsystems/playflic.md. */
#include "playflic.h"

/* @0x22c68 */
void IntroShowFrame(void)
{
    int i;

    while (!frame_ready)
        IntroTick();
    frame_ready = 0;
    if (credits_on) {
        for (i = 0; i < 3; i++) {
            if (credit_line[i])
                DrawText(I16(&credit_line_x[i]),
                         (short)(i * line_height + flic_height + 2),
                         credit_line[i]);
        }
    }
    memcpy(intro_dest, frame_image, frame_size);
}
