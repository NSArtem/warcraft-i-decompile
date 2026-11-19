/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * PlaceBoxPress (0x21af8, named in mod_20c30.toml): the map press handler that
 * PlaceBoxStart installs while the placement box is up.  It sends the 3-byte
 * cancel packet (type 5) so the partner's box closes too, and locks the status
 * panel.  Receiver: PacketDispatch row 5 -> PlaceBoxCancel 0x22930. */
#include "packet.h"

/* @0x21af8 */
void PlaceBoxPress(void *evt)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_PLACE_CANCEL;
    fn_214d4(3, msg);
    StatusPanelLockAdjust(1);
}
