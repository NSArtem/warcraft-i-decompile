/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x206c8 NetModemCommand: send an AT command line over the escaped framing -
 * one frame per character, then the CR terminator. */
#include <string.h>
#include <dos.h>
#include "network.h"

void NetModemCommand(const char *cmd)
{
    short i;
    const char *p = cmd;

    for (i = 0; i < strlen(cmd); i++) {
        NetSerialQueueBytes((const unsigned char *)p++, 1);
        delay(0x14);
    }
    NetSerialQueueBytes((const unsigned char *)net_cr, 1);
}
