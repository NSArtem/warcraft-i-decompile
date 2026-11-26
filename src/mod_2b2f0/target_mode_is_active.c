/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_2b2f0.h"

extern unsigned short net_event_pending;

/* @0x2b308 */
unsigned short TargetModeIsActive(void)
{
    return target_mode_flags[net_event_pending];
}
