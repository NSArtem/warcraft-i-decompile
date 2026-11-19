/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndScreenAnimate (0x2f9b4): count each of the 13 score numbers towards
 * its target by its step; returns 1 (after a redraw and a tick sound) while
 * anything is still moving. */
#include "mod_2efd0.h"

/* @0x2f9b4 */
int EndScreenAnimate(void)
{
    unsigned short i;
    int moved;
    long v;
    long t;

    moved = 0;
    i = 0;
    while (i != 13) {
        v = end_screen_value[i];
        t = end_screen_target[i];
        if (v < t) {
            moved = 1;
            v += end_value_step[i];
            end_screen_value[i] = v;
            if (v > t)
                end_screen_value[i] = t;
        }
        i++;
    }
    if (moved) {
        EndScreenDraw();
        ScreenUpdate();
        SndPlay(0);
        return 1;
    }
    return 0;
}
