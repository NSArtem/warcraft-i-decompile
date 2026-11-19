/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndScreenStop (0x2fa24): the "leave the end screen" path (the other
 * machine quit) sets the done flag the movie loop polls. */
#include "mod_2efd0.h"

/* @0x2fa24 */
void EndScreenStop(void)
{
    end_screen_done = 1;
}
