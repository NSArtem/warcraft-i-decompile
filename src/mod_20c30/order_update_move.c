/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * OrderUpdateMove (0x222e8, PLACEBOX.C): order 3 of the unit order table
 * (0x5158c/0x51598), the move order.  Returns 1 when the order finished.
 * docs/subsystems/mod_13f60.md section 1 for the dispatch contract. */
#include "mod_20c30.h"

unsigned short UnitMoveOrderCheck(Unit *u);             /* 0x11004 */
unsigned short fn_2207c(Unit *u);  /* UnitClearTargets, 0x2207c */
unsigned short fn_2220c(Unit *u, unsigned char arg);  /* OrderTargetInRange, 0x2220c */
unsigned short UnitAdvanceOrder(Unit *u, int use_arg);  /* 0x2edac */
void UnitSetOrder(Unit *u, unsigned char order);        /* 0x2ee50 */
unsigned short PathFind(Unit *u);                       /* 0x2cc54 */
unsigned short WorkerReturnToMine(Unit *u);             /* 0x21df0 */
unsigned short PathAdvanceFacing(Unit *u, Point *out);  /* 0x2c538 */
void MoveOrderTick(Unit *u, Point *dest);               /* 0x21f90 */
void fn_13954(Unit *u);                                 /* 0x13954 */
void fn_13928(Unit *u);                                 /* 0x13928 */
void fn_2ea4c(Unit *u);                                 /* 0x2ea4c */

/* @0x222e8 */
unsigned short OrderUpdateMove(Unit *u)
{
    Point p;

    if (UnitMoveOrderCheck(u) != 0)
        return 1;
    if (fn_2207c(u) != 0) {
        if (fn_2220c(u, u->order_next2) == 0)
            goto advance_path;
    }
    if (UnitAdvanceOrder(u, 1) == 0)
        UnitSetOrder(u, 2);
    return 1;

advance_path:
    if (PathFind(u) == 0) {
        if (WorkerReturnToMine(u) == 0)
            UnitSetOrder(u, 2);
        return 1;
    }
    if (PathAdvanceFacing(u, &p) == 0) {
        MoveOrderTick(u, &p);
        return 1;
    }
    fn_13954(u);
    *(Point *)&u->tx = p;
    fn_13928(u);
    fn_2ea4c(u);
    return 0;
}
