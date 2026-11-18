/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLG_SET.C): the four callbacks of the numeric field of
 * the 'Network Connection' dialog 0x185 (the node number). */
#include <stdio.h>
#include <stdlib.h>

#include "mod_13f60.h"

/* @0x15ebc */

void NumberParse(Control *c)
{
    edit_value = atoi(c->text);
    if (edit_value >= 100)
        edit_value = 0;
    sprintf(c->text, fmt_two_digits, edit_value);
}

/* @0x15f28 */
