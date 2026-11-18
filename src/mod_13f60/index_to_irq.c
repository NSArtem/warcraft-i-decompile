/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLG_SET.C): the baud-rate and IRQ <-> index conversions of
 * the modem/serial setup dialogs, each with its FatalError tag as the
 * unreachable default. */
#include "mod_13f60.h"

/* @0x1532c: 2400/4800/9600/19200/38400 -> 0..4 */

int IndexToIrq(int index)
{
    if (index == 0)
        return 2;
    if (index == 1)
        return 3;
    if (index == 2)
        return 4;
    if (index == 3)
        return 5;
    if (index == 4)
        return 7;
    FatalError(tag_idx2irq);
    return 0;
}
