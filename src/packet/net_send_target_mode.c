/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendTargetMode (0x21980): ask the partner to enter order-target mode.
 * The command card's "move"/"attack"/"harvest"/"repair"/targeted-spell
 * actions set pending_order and jump here; the receiver runs PlaceBox-free
 * target mode (TargetModeEnter) and locks its status panel.
 * docs/subsystems/packet.md; analysis/symbols/packet.toml. */
#include "packet.h"

/* @0x21980 */
void NetSendTargetMode(void)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_TARGET_MODE;
    PacketSend(3, msg);
    StatusPanelLockAdjust(1);
}
