/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern void UnitResetPath(void *u);                     /* 0x2cebc */
extern void UnitSetNextOrder(void *u, unsigned char o); /* 0x2eeac */
extern unsigned short fn_2207c(Unit *u);                /* 0x2207c */
extern unsigned short fn_2220c(Unit *u, unsigned char arg); /* 0x2220c */

/* @0x22464 */
void UnitOrderTargetFinish(Unit *u)
{
    unsigned char *p = (unsigned char *)u;
    unsigned o;

    UnitResetPath(u);
    p[0xf] &= 0xf;
    if (p[0x21] != 0x12) {
        PathSetReachableDest(u);
    }
    if (fn_2207c(u) == 0) {
        UnitSetNextOrder(u, 2);
        return;
    }
    o = p[0x21];
    if ((order_props[o] & 2) != 0) {
        if (o == 0x1f) {
            return;
        }
        UnitSetNextOrder(u, (unsigned char)o);
        return;
    }
    if (p[0x20] != 0x1f && fn_2220c(u, (unsigned char)o) == 0) {
        return;
    }
    o = p[0x21];
    if (o != 0x1f) {
        UnitSetNextOrder(u, (unsigned char)o);
    }
}
