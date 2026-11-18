/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLG_SET.C): the tick/checkbox action of the dialog
 * controls (the Tone/Pulse selector of the modem setup). */
#include "mod_13f60.h"

/* @0x15498: flip the integer the control points at. */
void CheckBoxToggle(Control *c)
{
    long *value = c->value;

    *value = *value == 0;
}
