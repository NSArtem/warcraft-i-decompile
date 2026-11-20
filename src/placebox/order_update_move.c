/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern int UnitMoveOrderCheck(Unit *u);                 /* 0x11004 */
extern int PathAdvanceFacing(Unit *u, Point *p);        /* 0x2c538 */
extern int PathFind(Unit *u);                           /* 0x2cc54 */
extern unsigned short UnitAdvanceOrder(Unit *u, int a); /* 0x2edac */
extern void UnitSetOrder(Unit *u, unsigned char o);     /* 0x2ee50 */
extern unsigned short fn_2207c(Unit *u);                /* 0x2207c */
extern unsigned short fn_2220c(Unit *u, unsigned char arg); /* 0x2220c */

/* @0x222e8 */
unsigned short OrderUpdateMove(Unit *u)
{
    Point dest;
    unsigned char *p = (unsigned char *)u;

    if ((short)UnitMoveOrderCheck(u) != 0) {
        return 1;
    }
    if (fn_2207c(u) == 0 || fn_2220c(u, p[0x21]) != 0) {
        if (UnitAdvanceOrder(u, 1) == 0) {
            UnitSetOrder(u, 2);
        }
        return 1;
    }
    if ((short)PathFind(u) == 0) {
        if (WorkerReturnToMine(u) == 0) {
            UnitSetOrder(u, 2);
        }
        return 1;
    }
    if ((short)PathAdvanceFacing(u, &dest) == 0) {
        MoveOrderTick(u, &dest);
        return 1;
    }
    fn_13954(u);
    *(Point *)(p + 0xa) = dest;
    fn_13928(u);
    fn_2ea4c(u);
    return 0;
}
