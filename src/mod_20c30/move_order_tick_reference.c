/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * MoveOrderTick (0x21f90, PLACEBOX.C): the arrival step of order 3 (move).
 * Plays the move sound, bumps the flags2 nibble, and decides between
 * "re-issue the order", "the order is done (stop)" and "reset the path".
 * Only caller: OrderUpdateMove 0x22389. */
#include "mod_20c30.h"

unsigned short fn_13348(short x, short y, unsigned mask);   /* 0x13348 */
void UnitResetPath(Unit *u);                           /* 0x2cebc */
void UnitSetNextOrder(Unit *u, unsigned char order);   /* 0x2eeac */
void fn_20f44(Unit *u);                                /* 0x20f44 */
extern unsigned short owner_block_mask[5];             /* 0x5189c */

/* @0x21f90 */
void MoveOrderTick(Unit *u, Point *dest)
{
    unsigned short nib;

    UnitStartAnim(u, order_sound[3]);
    u->anim_timer = 0x28;
    ((unsigned char *)u)[0xf] += 0x10;
    nib = u->flags2 & 0xf000;
    if (fn_13348(dest->x, dest->y, owner_block_mask[u->owner]) != 0) {
        if (u->type >= 2 && u->type <= 3)
            goto not_blocked;
        if (u->timer36 != 0 || u->attacker != 0)
            UnitResetPath(u);
        else
            UnitOrderTarget(u, dest->x, dest->y, 0, fn_20f44);
        u->anim_timer = 1;
        return;
    }
not_blocked:
    if (nib >= 0xf000) {
        ((unsigned char *)u)[0xf] &= 0xf;
        UnitSetNextOrder(u, 2);
        return;
    }
    if (nib < 0x8000 && TileOccupiedByUnit(u, dest) != 0) {
        if (nib == 0)
            WorkerReturnToMine(u);
        return;
    }
    UnitResetPath(u);
}
