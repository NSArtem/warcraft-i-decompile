/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_1bf80.h"

/* @0x1bf80 */
void WaitTickDown(void)
{
    wait_ticks_left--;
}
