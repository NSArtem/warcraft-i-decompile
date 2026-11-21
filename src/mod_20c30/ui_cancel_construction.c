/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern void NetSendCancelConstruction(Unit *u);

/* @0x20e78 */
void UiCancelConstruction(void)
{
    NetSendCancelConstruction(SelectionFirst(0x33));
}
