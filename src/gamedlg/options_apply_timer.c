/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* The Options page's timer callback: re-apply the sound options every 25 clock
 * ticks while the page is open, so a dragged volume slider takes effect at
 * once.  Returns 0 (the page loop's idle action). */
#include "gamedlg.h"

/* @0x1a778 */
int OptionsApplyTimer(struct OptionsParams *p)
{
    unsigned long t = clock();

    if (t > p->next_apply) {
        SndApplyOptions((const int *)p);
        p->next_apply = t + 0x19;
    }
    return 0;
}
