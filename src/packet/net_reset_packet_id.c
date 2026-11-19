/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * NetResetPacketId (0x21974, net_link.toml): the link layer's copy of
 * ResetPacketId, called by NetResetLink 0x12ca6 when a session starts. */
#include "packet.h"

/* @0x21974 */
void NetResetPacketId(void)
{
    packet_id = 0;
}
