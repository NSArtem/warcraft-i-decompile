/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendOrder (0x21a58): the general unit-order packet (type 9) - the target
 * cell (a Point at +3), the target unit and the pending order id.  The
 * command-card actions store pending_order and let the target click
 * (fn_2f0a8) call this; without a pending order it does nothing.  Receiver:
 * PacketDispatch row 9 looks the order up in order_handlers (0x52a80) and
 * applies it to the selection with fn_260c8.
 * The Point store is what the original compiled (`mov word [esp+3],cx` /
 * `[esp+5],si` from a Point *local); two separate short stores give the
 * other register assignment (watched on 2026-11-19). */
#include "packet.h"

/* @0x21a58 */
void NetSendOrder(short arg1, short arg2, Unit *target)
{
    unsigned char msg[PKT_BUF];
    Point *pt;

    if (pending_order == 0)
        return;
    msg[0] = PKT_ORDER;
    *(unsigned short *)(msg + 7) = (unsigned short)RefRelocate((int)target, (int)unit_array, 1);
    pt = (Point *)(msg + 3);
    pt->x = arg1;
    pt->y = arg2;
    *(unsigned short *)(msg + 9) = pending_order;
    fn_214d4(0xb, msg);
    StatusPanelLockAdjust(1);
    pending_order = 0;
}
