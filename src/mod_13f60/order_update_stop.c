/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern void UnitIdleTick(OrderUnit *u);
extern void AiWorkSiteStep(OrderUnit *u);
extern void UnitIdleTurn(OrderUnit *u);

/* @0x14030 */
int OrderUpdateStop(OrderUnit *u)
{
    int t;
    int ok;

    UnitIdleTick(u);
    if (*(short *)((char *)u + 0x14) != 0) {
        AiWorkSiteStep(u);
    } else if (u->order_next == 0x1f) {
        t = u->type;
        if (t <= 0x1f) {
            if (t < 4 || t > 5) {
                ok = 1;
            } else {
                ok = 0;
            }
            if (ok) {
                UnitIdleTurn(u);
            }
        }
    }
    return 1;
}
