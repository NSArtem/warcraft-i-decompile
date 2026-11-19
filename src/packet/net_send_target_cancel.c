/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendTargetCancel (0x219ac): leave order-target mode on both sides.
 * The Escape/cancel handler fn_1b5e8 jumps here while target mode is up, and
 * fn_2b31c installs this address as the cancel callback [0x59510].
 * Receiver: PacketDispatch row 8 -> fn_2b390 (target-mode teardown). */
#include "packet.h"

/* @0x219ac */
void NetSendTargetCancel(void)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_TARGET_CANCEL;
    fn_214d4(3, msg);
    StatusPanelLockAdjust(1);
}
