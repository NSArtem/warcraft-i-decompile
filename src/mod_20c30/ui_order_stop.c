/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern void UnitSetNextOrder(void *u, unsigned char order);

/* @0x20e88 */
void UiOrderStop(void *u)
{
    UnitSetNextOrder(u, 2);
}
