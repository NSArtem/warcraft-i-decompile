/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern unsigned short pending_order;
extern void NetSendTargetMode(void);

/* @0x2110c */
void UiSetPendingOrder14(void)
{
    pending_order = 14;
    NetSendTargetMode();
}
