/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13e60.h"

extern short dat_51530;

/* @0x13e94: reload the demo idle timer (DemoIdleTick decrements it; DemoRun
 * repeats the same store at 0x13f55). */
void DemoIdleTimerReset(void)
{
    dat_51530 = 0x10e;
}
