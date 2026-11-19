/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendPlaceConfirm (0x21b24): place the building at a map cell.
 * Caller PlaceBoxRelease (0x1b4dc) is the map release handler installed by
 * PlaceBoxStart; it packs the cell as x | y << 16.
 * Receiver: PacketDispatch row 6 -> PlaceBoxConfirm(cell) 0x22ae4. */
#include "packet.h"

/* @0x21b24 */
void NetSendPlaceConfirm(unsigned long cell)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_PLACE_CONFIRM;
    *(unsigned long *)(msg + 3) = cell;
    fn_214d4(7, msg);
    StatusPanelLockAdjust(1);
}
