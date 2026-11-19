/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetSendCheatFlags (0x21c44, named in mod_20c30.toml): send the cheat flag
 * word the local player just typed (type 0x10), so the partner applies the
 * same cheat.  Receiver: PacketDispatch row 0x10 -> SetCheatFlags. */
#include "packet.h"

/* @0x21c44 */
void NetSendCheatFlags(unsigned long flags)
{
    unsigned char msg[PKT_BUF];

    msg[0] = PKT_CHEAT_FLAGS;
    *(unsigned long *)(msg + 3) = flags;
    fn_214d4(7, msg);
}
