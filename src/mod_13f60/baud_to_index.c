/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLG_SET.C): the baud-rate and IRQ <-> index conversions of
 * the modem/serial setup dialogs, each with its FatalError tag as the
 * unreachable default. */
#include "mod_13f60.h"

/* @0x1532c: 2400/4800/9600/19200/38400 -> 0..4 */

int BaudToIndex(long baud)
{
    if (baud == 0x960)
        return 0;
    if (baud == 0x12c0)
        return 1;
    if (baud == 0x2580)
        return 2;
    if (baud == 0x4b00)
        return 3;
    if (baud == 0x9600)
        return 4;
    FatalError(tag_baud2idx);
    return 0;
}

/* @0x1538c: 0..4 -> 2400/4800/9600/19200/38400 */
