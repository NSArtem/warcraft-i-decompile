/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendCancelConstruction (0x21b54): remove the selected building and refund
 * it.  Caller fn_20e78 is the "cancel construction" card (it selects the unit
 * and tail-jumps here).  Receiver: PacketDispatch row 0xa -> fn_2e384, the
 * refund + detach + UnitRemove executor. */
#include "packet.h"

/* @0x21b54 */
void NetSendCancelConstruction(Unit *u)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_CANCEL_CONSTR;
    *(unsigned short *)(msg + 3) = (unsigned short)RefRelocate((int)u, (int)unit_array, 1);
    PacketSend(5, msg);
    StatusPanelLockAdjust(1);
}
