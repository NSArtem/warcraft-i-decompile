/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

struct Unit;
extern void UnitFinalizeGone(struct Unit *u);

/* @0x13f60 */
int OrderUpdateGone(OrderUnit *u)
{
    UnitFinalizeGone((struct Unit *)u);
    return 0;
}
