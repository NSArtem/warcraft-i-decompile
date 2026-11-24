/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x208d4 NetModemAnswer (docs/subsystems/network.md).
 * Verified differentially by tests/test_network.py (T4). */
#include "network.h"

static char rsp_ring[5] = "RING";

int NetModemAnswer(void)
{
    if (NetModemInit() == 0)
        return 0;
    if (NetModemWaitResponse(rsp_ring) == 0)
        return 0;
    NetModemCommand(net_cmd_answer);
    return NetModemWaitResponse(net_rsp_connect);
}
