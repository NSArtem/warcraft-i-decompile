/* codegen-compiler: 10.0a */
#include "mod_2b400_f1.h"
#include <stdio.h>

extern void DrawText(short x, short y, const char *s); /* 0x31dcc; called at 0x2b810 */

/* 0x2b7c4: advance the count at 0x2b7d3..0x2b7f5, then format and draw. */
void DrawAnimatedResourceCounter(const char *format, short x, short y,
                                 int *displayed_count, int target_count)
{
    char buffer[128];
    int delta;
    int step;

    delta = target_count - *displayed_count;
    if (delta != 0) {
        step = delta / 16;
        if (delta > 0)
            ++step;
        else
            --step;
        *displayed_count += step;
    }
    sprintf(buffer, format, *displayed_count);
    DrawText(x, y, buffer);
}
