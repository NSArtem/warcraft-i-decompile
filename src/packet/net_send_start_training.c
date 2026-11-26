/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendStartTraining (0x21bc4): start the selected building's unit training.
 * Caller fn_2132c is the "train <unit>" / "build catapult" card; the cost is
 * charged by the receiver's UnitStartTraining(SelectionFirst(), type).
 * Receiver: PacketDispatch row 0xc -> UnitStartTraining 0x115f4. */
#include "packet.h"

/* @0x21bc4 */
void NetSendStartTraining(unsigned char type)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_START_TRAINING;
    msg[3] = type;
    PacketSend(4, msg);
    StatusPanelLockAdjust(1);
}
