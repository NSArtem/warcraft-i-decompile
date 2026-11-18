/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DGLS.C): the two side totals of the 'Set Army' dialog. */
#include <stdio.h>

#include "mod_13f60.h"

/* @0x14d04: sum the two halves of the 14 army counts and print each total. */
void ArmyTotalsText(unsigned long *army)
{
    unsigned long total = 0;
    unsigned long *p = army;
    int i;

    for (i = 0; i < 7; i++, p++)
        if (*p > 1)
            total += *p - 1;
    sprintf(dat_59230, fmt_decimal, total);
    total = 0;
    for (i = 0; i < 7; i++, p++)
        if (*p > 1)
            total += *p - 1;
    sprintf(edit_buffer1, fmt_decimal, total);
}
