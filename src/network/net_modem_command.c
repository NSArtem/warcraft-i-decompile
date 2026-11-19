/* codegen-compiler: 10.0a */
/* 0x206c8 NetModemCommand: send an AT command line over the escaped framing -
 * one frame per character, then the CR terminator. */
#include <string.h>
#include <dos.h>
#include "network.h"

void NetModemCommand(const char *cmd)
{
    const char *p = cmd;
    short i;

    for (i = 0; i < strlen(cmd); i++) {
        NetSerialSend(p++, 1);
        delay(0x14);
    }
    NetSerialSend(net_cr, 1);
}
