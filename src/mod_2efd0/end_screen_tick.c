/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndScreenTick (0x2f930): dialog_idle hook of the win/lose screen; counts
 * 1/18 s ticks, EndScreenMovie advances the movie every second tick. */
#include "mod_2efd0.h"

/* @0x2f930 */
void EndScreenTick(void)
{
    end_screen_ticks++;
}
