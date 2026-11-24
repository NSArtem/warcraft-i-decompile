/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
#include "mod_13f60.h"

extern unsigned char fn_1de60(unsigned long from, unsigned long to);
extern unsigned char fn_1def0(OrderUnit *u);
extern void SpellCastOrder(OrderUnit *u);
extern short fn_2eefc(OrderUnit *u, void (*cb)(OrderUnit *), int flag);
extern void fn_21168(OrderUnit *u);
extern unsigned char order_props[32];
extern unsigned short spell_order;

/* @0x14140 */
int OrderUpdateSpell(OrderUnit *u)
{
    unsigned short p;

    spell_order = u->order;
    p = order_props[u->order];
    if ((p & 1) != 0) {
        if ((p & 4) != 0 && *(void **)((char *)u + 0x52) == 0) {
            u->facing = fn_1de60(*(unsigned long *)((char *)u + 0xa), *(unsigned long *)((char *)u + 0x4e));
        } else {
            if ((p & 2) == 0) {
                if (fn_2eefc(u, fn_21168, 1) != 0) {
                    goto done;
                }
            }
            u->facing = fn_1def0(u);
        }
    }
    SpellCastOrder(u);
done:
    spell_order = 0;
    return 1;
}
