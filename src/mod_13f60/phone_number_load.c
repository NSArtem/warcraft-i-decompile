/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DLG_SET.C): the edit-control callbacks of the modem
 * connection dialog 0x182. */
#include "mod_13f60.h"

/* @0x15568: put the stored dial string into the control's text buffer. */
void PhoneNumberLoad(Control *c)
{
    strcpy(c->text, phone_number);
}
