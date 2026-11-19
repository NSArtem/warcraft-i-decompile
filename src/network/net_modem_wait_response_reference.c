/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x20900 NetModemWaitResponse (docs/subsystems/network.md).
 *
 * The original is ONE function split into two blocks by the compiler: the
 * prologue and the result-table loop at 0x20900 and the byte-reading block at
 * 0x2070e, which code discovery reports as a separate start (it has no
 * prologue, reads the caller's frame and its `ret` pops that frame).  This
 * file therefore holds the whole function; the T4 test calls the original
 * entry 0x20900, which runs both blocks.
 */
#include <string.h>
#include "network.h"

static char rsp_busy[5] = "BUSY";
static char rsp_error[6] = "ERROR";
static char rsp_no_carrier[11] = "NO CARRIER";
static char rsp_no_dialtone[13] = "NO DIALTONE";
static char rsp_no_answer[10] = "NO ANSWER";

#if 0
/* 0x2070e NetModemWaitResponse_tail is a block of the function below, not a
 * callable function: entered by the conditional jump at 0x20930, it appends
 * one received byte and, at the end of a line, matches the result table. */
int NetModemWaitResponse_tail(const char *expect, int len);
#endif

int NetModemWaitResponse(const char *expect)
{
    char *results[5];
    unsigned short i;
    short len;
    int c;

    results[0] = rsp_busy;
    results[1] = rsp_error;
    results[2] = rsp_no_carrier;
    results[3] = rsp_no_dialtone;
    results[4] = rsp_no_answer;
    len = 0;
    for (;;) {
        if (key_down_table[1] != 0 || key_down_table[1] != key_down_table[46]) {
            net_response[0] = 0;
            return 0;
        }
        c = NetSerialGetByte();
        if (c == -1)
            continue;
        if (c == 0x0a || len == 0x4f) {
            net_response[len] = 0;
            for (i = 0; i < 5; i++) {
                if (strncmp(net_response, results[i], strlen(results[i])) == 0) {
                    if (i >= 2)
                        strcpy(net_error_text, results[i]);
                    return 0;
                }
            }
            if (strncmp(net_response, expect, strlen(expect)) == 0)
                return 1;
            len = 0;
        } else if (c >= 0x20) {
            net_response[len++] = (char)c;
        }
    }
}
