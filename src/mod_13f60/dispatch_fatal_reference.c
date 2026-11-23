/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern const char order_dispatch_error[11];

/* @0x145d0 */
int DispatchFatal(OrderUnit *u)
{
    FatalError(order_dispatch_error);
    return 0;
}
