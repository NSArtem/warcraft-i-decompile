/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLG_SET.C): the baud-rate and IRQ <-> index conversions of
 * the modem/serial setup dialogs, each with its FatalError tag as the
 * unreachable default. */
#include "mod_13f60.h"

/* @0x1532c: 2400/4800/9600/19200/38400 -> 0..4 */

int IrqToIndex(int irq)
{
    if (irq == 2)
        return 0;
    if (irq == 3)
        return 1;
    if (irq == 4)
        return 2;
    if (irq == 5)
        return 3;
    if (irq == 7)
        return 4;
    FatalError(tag_irq2idx);
    return 0;
}

/* @0x1543c: 0..4 -> IRQ 2/3/4/5/7 */
