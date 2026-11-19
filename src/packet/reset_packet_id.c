/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * ResetPacketId (0x21968, net_link.toml): clear the outgoing packet id.
 * Callers: fn_195ac 0x19799 (the scenario start) and NetLoadSyncMessage
 * 0x245a4 (before the load handshake).  0x21974 is the identical copy the
 * link layer uses (NetResetLink). */
#include "packet.h"

/* @0x21968 */
void ResetPacketId(void)
{
    packet_id = 0;
}
