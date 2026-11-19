/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendCancelProduction (0x21bf4): cancel the selected building's training
 * or upgrade.  The "cancel unit training" card is the thunk fn_20e70, which
 * is just `jmp` here.  Receiver: PacketDispatch row 0xd ->
 * UnitCancelProduction(SelectionFirst()). */
#include "packet.h"

/* @0x21bf4 */
void NetSendCancelProduction(void)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_CANCEL_PRODUCTION;
    fn_214d4(3, msg);
    StatusPanelLockAdjust(1);
}
