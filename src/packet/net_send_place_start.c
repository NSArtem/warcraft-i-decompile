/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendPlaceStart (0x21ac8): start building placement on both sides.
 * The build cards (fn_212ac, e.g. "build farm" arg 0x20) check and refund the
 * cost here; the receiver's PlaceBoxStart pays for it (PlaceBoxConfirm).
 * Receiver: PacketDispatch row 4 -> PlaceBoxStart(type) 0x22798. */
#include "packet.h"

/* @0x21ac8 */
void NetSendPlaceStart(unsigned char type)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_PLACE_START;
    msg[3] = type;
    fn_214d4(4, msg);
    StatusPanelLockAdjust(1);
}
