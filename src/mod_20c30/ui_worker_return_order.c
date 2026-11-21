/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern unsigned char dat_5008c[];
extern unsigned short fn_13348(int x, int y, unsigned mask);
extern void UnitSetNextOrders(void *u, unsigned char order, unsigned char order2);

/* @0x20ed4 */
void UiWorkerReturnOrder(void *u)
{
    Unit *p = (Unit *)u;
    unsigned char o;

    if (dat_5008c[*((unsigned char *)p + 0x1e)] != 1) {
        if (*(long *)((char *)p + 0x52) != 0) {
            o = 5;
        } else if (fn_13348((int)(*(long *)((char *)p + 0x4c) >> 16), (int)(*(long *)((char *)p + 0x4e) >> 16), 0xc) != 0) {
            o = 7;
        } else {
            o = 6;
        }
    } else {
        o = 6;
    }
    UnitSetNextOrders(u, 3, o);
}
