/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern unsigned short pending_order;
extern void NetSendTargetMode(void);

/* @0x21030 */
void UiSetPendingOrder4(void)
{
    pending_order = 4;
    NetSendTargetMode();
}
