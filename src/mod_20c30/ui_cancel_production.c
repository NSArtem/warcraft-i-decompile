/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern void NetSendCancelProduction(void);

/* @0x20e70 */
void UiCancelProduction(void)
{
    NetSendCancelProduction();
}
