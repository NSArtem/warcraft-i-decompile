/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendStartResearch (0x21b94): start the selected building's upgrade.
 * Caller fn_212e8 is the "research <upgrade>" card; the cost is charged by
 * the receiver's UnitStartResearch(SelectionFirst(), row).
 * Receiver: PacketDispatch row 0xb -> UnitStartResearch 0x11538. */
#include "packet.h"

/* @0x21b94 */
void NetSendStartResearch(unsigned char row)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_START_RESEARCH;
    msg[3] = row;
    PacketSend(4, msg);
    StatusPanelLockAdjust(1);
}
