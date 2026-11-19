/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* REFERENCE C for 0x1f62c NetSerialConnect (docs/subsystems/network.md): the
 * four-word serial handshake ("listen"/"talk"/"waiting"/"ack") with the
 * dial/answer prelude in modem mode.  Verified differentially by
 * tests/test_network.py (T4). */
#include <string.h>
#include <dos.h>
#include "network.h"

void delay(unsigned ms);                 /* 0x31784 */

static char cmd_listen[7] = "listen";
static char cmd_talk[5] = "talk";
static char cmd_waiting[8] = "waiting";
static char cmd_ack[4] = "ack";
static char rsp_busy[5] = "BUSY";

int NetSerialConnect(void)
{
    unsigned short done = 0;
    unsigned short node = 0;
    unsigned long deadline;
    char line[NET_FRAME_MAX];
    short i;

    if (net_modem_link != 0) {
        if (own_campaign != 0) {
            while (NetModemDial() == 0)
                if (strncmp(net_response, rsp_busy, 4) != 0)
                    return 0;
        } else if (NetModemAnswer() == 0) {
            return 0;
        }
    }
    line[0] = 0;
    NetSerialDrain();
    for (;;) {
        deadline = (unsigned long)clock() + 0x64;
        for (;;) {
            if (node != key_down_table[1] || node != key_down_table[46])
                return 0;
            if (NetSerialReceive(line) != 0) {
                if (strcmp(line, cmd_listen) == 0) {
                    NetSerialSend(cmd_talk, 5);
                    NetSerialSend(cmd_listen, 7);
                    NetSerialSend(cmd_listen, 7);
                    NetSerialSend(cmd_listen, 7);
                    delay(0xfa);
                    done = 1;
                } else if (strcmp(line, cmd_talk) == 0) {
                    done = 1;
                } else if (strcmp(line, cmd_waiting) == 0) {
                    NetSerialSend(cmd_ack, 4);
                } else if (strcmp(line, cmd_ack) == 0) {
                    NetSerialSend(cmd_ack, 4);
                    NetSerialSend(cmd_ack, 4);
                    NetSerialSend(cmd_ack, 4);
                    done = 1;
                    delay(0xfa);
                }
                break;
            }
            if ((unsigned long)clock() >= deadline)
                break;
        }
        NetSerialSend(cmd_waiting, 8);
        if (done != 0) {
            NetSerialDrain();
            return 1;
        }
    }
}
