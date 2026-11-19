/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x20884 NetModemDial (docs/subsystems/network.md).
 * Verified differentially by tests/test_network.py (T4). */
#include <stdio.h>
#include "network.h"

static char cmd_atdp[7] = "ATDP%s";
static char cmd_atdt[7] = "ATDT%s";
static char rsp_connect[8] = "CONNECT";

int NetModemDial(void)
{
    char cmd[0x50];

    if (NetModemInit() == 0)
        return 0;
    sprintf(cmd, dial_pulse != 0 ? cmd_atdp : cmd_atdt, phone_number);
    NetModemCommand(cmd);
    return NetModemWaitResponse(rsp_connect);
}
