/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x207c0 NetModemInit (docs/subsystems/network.md): the
 * ATZ / init-string negotiation; a response that starts with "ERROR" stores
 * the matching text in net_error_text.  Verified differentially by
 * tests/test_network.py (T4). */
#include <string.h>
#include <dos.h>
#include "network.h"

static char rsp_ok[3] = "OK";
static char rsp_error[6] = "ERROR";
static char err_init[28] = "Error in modem init string.";

int NetModemInit(void)
{
    if (modem_init1[0] != 0) {
        NetModemCommand(modem_init1);
        if (NetModemWaitResponse(rsp_ok) == 0) {
            if (strncmp(net_response, rsp_error, 4) == 0)
                memcpy(net_error_text, net_err_reset, 23);
            return 0;
        }
    }
    delay(0xfa);
    if (modem_init2[0] != 0) {
        NetModemCommand(modem_init2);
        if (NetModemWaitResponse(rsp_ok) == 0) {
            if (strncmp(net_response, rsp_error, 4) == 0)
                memcpy(net_error_text, err_init, sizeof(err_init));
            return 0;
        }
    }
    delay(0xfa);
    return 1;
}
