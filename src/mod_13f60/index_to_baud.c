/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLG_SET.C): the baud-rate and IRQ <-> index conversions of
 * the modem/serial setup dialogs, each with its FatalError tag as the
 * unreachable default. */
#include "mod_13f60.h"

/* @0x1532c: 2400/4800/9600/19200/38400 -> 0..4 */

long IndexToBaud(int index)
{
    if (index == 0)
        return 0x960;
    if (index == 1)
        return 0x12c0;
    if (index == 2)
        return 0x2580;
    if (index == 3)
        return 0x4b00;
    if (index == 4)
        return 0x9600;
    FatalError(tag_idx2baud);
    return 0;
}

/* @0x153e8: IRQ 3/4/5/7 -> 1..4 */
