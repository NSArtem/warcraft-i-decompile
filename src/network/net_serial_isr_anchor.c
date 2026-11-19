/* codegen-compiler: 10.0a */
/* 0x202bc NetSerialIsrAnchor: a single `ret`, used only as the address that
 * NetSerialStart's DpmiLockRegion call keeps resident (the page of the two
 * interrupt handlers). */
#include "network.h"

void NetSerialIsrAnchor(void)
{
}
