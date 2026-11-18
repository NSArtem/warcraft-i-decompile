/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLG_SET.C): the four callbacks of the numeric field of
 * the 'Network Connection' dialog 0x185 (the node number). */
#include <stdio.h>
#include <stdlib.h>

#include "mod_13f60.h"

/* @0x15ebc */

void NumberFormat(Control *c)
{
    sprintf(c->text, fmt_two_digits, net_node_number);
    edit_control = c;
}

/* @0x15ee4 */
