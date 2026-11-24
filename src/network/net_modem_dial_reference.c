/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x20884 NetModemDial (docs/subsystems/network.md).
 * Verified differentially by tests/test_network.py (T4). */
#include <stdio.h>
#include "network.h"

int NetModemDial(void)
{
    char cmd[0x50];

    if (NetModemInit() == 0)
        return 0;
    sprintf(cmd, dial_pulse != 0 ? net_cmd_atdp : net_cmd_atdt, phone_number);
    NetModemCommand(cmd);
    return NetModemWaitResponse(net_rsp_connect);
}
